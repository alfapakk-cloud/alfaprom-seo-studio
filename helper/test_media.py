# -*- coding: utf-8 -*-
import base64
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import media


def webp(width=640, height=480):
    payload = b'\x00\x00\x00\x9d\x01\x2a' + struct.pack('<HH', width, height) + b'\x00\x00'
    body = b'WEBPVP8 ' + struct.pack('<I', len(payload)) + payload
    return b'RIFF' + struct.pack('<I', len(body)) + body


class MediaTests(unittest.TestCase):
    def test_webp_dimensions_and_container_length(self):
        self.assertEqual(media.webp_dimensions(webp()), (640, 480))
        for data in [b'\x89PNG\r\n\x1a\n' + b'0' * 40, webp()[:-1], webp() + b'junk', webp(8193, 1), webp(8000, 8000)]:
            with self.assertRaises(ValueError):
                media.webp_dimensions(data)

    def test_animation_is_rejected(self):
        body = b'WEBPVP8X' + struct.pack('<I', 10) + b'\x02\x00\x00\x00' + (639).to_bytes(3, 'little') + (479).to_bytes(3, 'little')
        with self.assertRaisesRegex(ValueError, 'Анимация'):
            media.webp_dimensions(b'RIFF' + struct.pack('<I', len(body)) + body)

    def test_saved_asset_survives_new_read_and_is_immutable(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(media, 'ASSET_ROOT', Path(folder)):
            first = media.save_asset(base64.b64encode(webp()).decode())
            second = media.save_asset(base64.b64encode(webp()).decode())
            self.assertNotEqual(first['assetId'], second['assetId'])
            self.assertEqual(first['file'], 'images/' + first['assetId'] + '.webp')
            read = media.read_asset(first['assetId'])
            self.assertEqual(base64.b64decode(read['base64']), webp())
            self.assertEqual((read['width'], read['height']), (640, 480))

    def test_invalid_identifiers_base64_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(media, 'ASSET_ROOT', Path(folder)):
            for value in ['../../secret', 'A' * 32, 'a' * 31, None]:
                with self.assertRaises(ValueError):
                    media.read_asset(value)
            for value in ['!invalid', base64.b64encode(b'PNG pretending to be WebP').decode(), None]:
                with self.assertRaises(ValueError):
                    media.save_asset(value)
            with self.assertRaisesRegex(ValueError, 'не найден'):
                media.read_asset('a' * 32)

    def test_symlink_asset_is_not_read(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(media, 'ASSET_ROOT', Path(folder)):
            target = Path(folder) / 'target';target.write_bytes(webp())
            (Path(folder) / ('a' * 32 + '.webp')).symlink_to(target)
            with self.assertRaises(ValueError):
                media.read_asset('a' * 32)

    def test_imagegen_path_must_be_real_and_inside_generated_images(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'CODEX_HOME': folder}):
            root = Path(folder);allowed = root / 'generated_images' / 'session';allowed.mkdir(parents=True)
            image = allowed / 'image.png';image.write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 30)
            self.assertEqual(media.read_generated_image(str(image))['mime'], 'image/png')
            outside = root / 'outside.png';outside.write_bytes(image.read_bytes())
            for path in [str(outside), str(allowed / 'missing.png')]:
                with self.assertRaises(ValueError):
                    media.read_generated_image(path)
            (allowed / 'escape.png').symlink_to(outside)
            with self.assertRaises(ValueError):
                media.read_generated_image(str(allowed / 'escape.png'))


    def test_rgba_fallback_encodes_real_webp_and_saves(self):
        raw = b'APRGBA01' + struct.pack('<II', 32, 20) + bytes([40, 120, 210, 255]) * (32 * 20)
        with tempfile.TemporaryDirectory() as folder, patch.object(media, 'ASSET_ROOT', Path(folder)):
            result = media.save_asset(base64.b64encode(raw).decode('ascii'))
            stored = media.read_asset(result['assetId'])
            data = base64.b64decode(stored['base64'])
            self.assertEqual(media.webp_dimensions(data), (32, 20))
            self.assertEqual(data[:4], b'RIFF')
            self.assertNotIn('base64', result)

    def test_rgba_rejects_truncated_oversized_and_inconsistent_buffers(self):
        for raw in [b'APRGBA01', b'APRGBA01' + struct.pack('<II', 0, 4), b'APRGBA01' + struct.pack('<II', 2000, 1) + b'x' * 8000, b'APRGBA01' + struct.pack('<II', 32, 20) + b'x' * 12]:
            with patch.object(media.ctypes, 'CDLL') as load:
                with self.assertRaises(ValueError):
                    media.encode_rgba(raw)
                load.assert_not_called()

    def test_full_cover_buffer_fits_route_limit_and_encodes(self):
        raw = b'APRGBA01' + struct.pack('<II', 1680, 720) + bytes([200, 100, 45, 255]) * (1680 * 720)
        self.assertLess(len(base64.b64encode(raw)), 8_000_000)
        self.assertEqual(media.webp_dimensions(media.encode_rgba(raw)), (1680, 720))


if __name__ == '__main__':
    unittest.main()
