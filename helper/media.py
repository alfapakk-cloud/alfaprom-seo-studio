# -*- coding: utf-8 -*-
"""Local generated media storage; no third-party service or image API."""
import base64
import json
import os
from pathlib import Path
import re
import secrets
import struct

MAX_IMAGE = 12_000_000
ASSET_ROOT = Path.home() / 'Library/Application Support/ALFAPROM SEO Studio/assets'


def webp_dimensions(data):
    if not isinstance(data, bytes) or len(data) < 30 or len(data) > MAX_IMAGE:
        raise ValueError('Некорректный размер WebP.')
    if data[:4] != b'RIFF' or data[8:12] != b'WEBP' or struct.unpack('<I', data[4:8])[0] + 8 != len(data):
        raise ValueError('Нужен настоящий WebP, а не переименованный PNG/JPEG.')
    offset, dimensions = 12, None
    while offset + 8 <= len(data):
        kind = data[offset:offset + 4]
        size = struct.unpack('<I', data[offset + 4:offset + 8])[0]
        payload = data[offset + 8:offset + 8 + size]
        if len(payload) != size:
            raise ValueError('WebP повреждён.')
        if kind == b'VP8X' and size >= 10:
            if payload[0] & 2:
                raise ValueError('Анимация не подходит для иллюстрации статьи.')
            dimensions = (1 + int.from_bytes(payload[4:7], 'little'), 1 + int.from_bytes(payload[7:10], 'little'))
        elif kind == b'VP8 ' and size >= 10 and payload[3:6] == b'\x9d\x01\x2a':
            dimensions = (int.from_bytes(payload[6:8], 'little') & 0x3fff, int.from_bytes(payload[8:10], 'little') & 0x3fff)
        elif kind == b'VP8L' and size >= 5 and payload[0] == 0x2f:
            bits = int.from_bytes(payload[1:5], 'little')
            dimensions = (1 + (bits & 0x3fff), 1 + ((bits >> 14) & 0x3fff))
        offset += 8 + size + (size & 1)
    if not dimensions or not all(1 <= n <= 8192 for n in dimensions) or dimensions[0] * dimensions[1] > 20_000_000:
        raise ValueError('Не удалось проверить размеры WebP.')
    return dimensions


def asset_path(asset_id):
    if not isinstance(asset_id, str) or not re.fullmatch('[a-f0-9]{32}', asset_id):
        raise ValueError('Некорректный идентификатор изображения.')
    root = ASSET_ROOT.resolve()
    path = root / (asset_id + '.webp')
    if path.is_symlink():
        raise ValueError('Ссылка вместо файла изображения запрещена.')
    return path


def save_asset(encoded):
    if not isinstance(encoded, str) or len(encoded) > 8_000_000:
        raise ValueError('Слишком большой файл изображения.')
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise ValueError('Некорректные данные изображения.')
    width, height = webp_dimensions(data)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    asset_id = secrets.token_hex(16)
    with asset_path(asset_id).open('xb') as stream:
        stream.write(data)
    return {'assetId': asset_id, 'file': 'images/' + asset_id + '.webp', 'mime': 'image/webp',
            'width': width, 'height': height, 'bytes': len(data)}


def read_asset(asset_id):
    path = asset_path(asset_id)
    if not path.is_file() or path.stat().st_size > MAX_IMAGE:
        raise ValueError('Файл изображения не найден на этом Mac. Используйте сохранённый ZIP-пакет.')
    data = path.read_bytes()
    width, height = webp_dimensions(data)
    return {'assetId': asset_id, 'file': 'images/' + asset_id + '.webp', 'mime': 'image/webp',
            'width': width, 'height': height, 'bytes': len(data), 'base64': base64.b64encode(data).decode('ascii')}


def read_generated_image(filename):
    if not isinstance(filename, str) or not filename:
        raise ValueError('imagegen не вернул путь к изображению.')
    base = (Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'generated_images').resolve()
    path = Path(filename).expanduser().resolve()
    if base not in path.parents or not path.is_file() or not 30 <= path.stat().st_size <= MAX_IMAGE:
        raise ValueError('Путь не указывает на реальный файл встроенного imagegen.')
    data = path.read_bytes()
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
    elif data.startswith(b'\xff\xd8\xff'):
        mime = 'image/jpeg'
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        webp_dimensions(data)
        mime = 'image/webp'
    else:
        raise ValueError('imagegen вернул неподдерживаемый формат файла.')
    return {'mime': mime, 'base64': base64.b64encode(data).decode('ascii'), 'bytes': len(data)}
