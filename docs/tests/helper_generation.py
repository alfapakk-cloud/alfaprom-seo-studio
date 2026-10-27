#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exercise the real Codex result handler without inference, login or user files."""
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('helper_under_test', ROOT / 'helper/alfaprom_helper.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class GenerationBridgeTests(unittest.TestCase):
    def run_result(self, result, operation='generate'):
        test = self

        class CodexProcess:
            pid = 999999
            returncode = 0

            def __init__(self, command, **kwargs):
                test.assertIn('forced_login_method="chatgpt"', command)
                test.assertEqual(command[command.index('--model') + 1], 'gpt-6.1-sol')
                test.assertIn('model_reasoning_effort="high"', command)
                test.assertNotIn('OPENAI_API_KEY', kwargs['env'])
                schema = json.loads(Path(command[command.index('--output-schema') + 1]).read_text())
                if operation == 'generate' and isinstance(result.get('visuals'), list):
                    bounds = schema['properties']['visuals']
                    test.assertTrue(bounds['minItems'] <= len(result['visuals']) <= bounds['maxItems'])
                self.output = Path(command[command.index('--output-last-message') + 1])

            def communicate(self, instruction, timeout):
                self.output.write_text(json.dumps(result), encoding='utf-8')
                return None, None

        with patch.object(helper, 'codex_binary', return_value='/mock/codex'), \
                patch.object(helper.subprocess, 'Popen', CodexProcess), \
                patch.dict(helper.os.environ, {'OPENAI_API_KEY': 'test-key-never-used'}):
            return helper.execute_task('Isolated result fixture, not a model call.', 'regression-job-171', operation)

    @staticmethod
    def fixture(count):
        return {'html': '<h2>Test</h2><p>Article</p>',
                'seo': {'title': 'Title', 'description': 'Description', 'h1': 'H1'},
                'visuals': [{'id': 'cover' if n == 0 else 'v%02d' % n,
                             'kind': 'cover' if n == 0 else 'photo'} for n in range(count)],
                'verificationNotes': []}

    def test_current_small_body_four_and_cover(self):
        self.assertEqual(len(self.run_result(self.fixture(5))['visuals']), 5)

    def test_current_medium_body_six_and_cover(self):
        self.assertEqual(len(self.run_result(self.fixture(7))['visuals']), 7)

    def test_current_large_body_ten_and_cover(self):
        self.assertEqual(len(self.run_result(self.fixture(11))['visuals']), 11)

    def test_legacy_formats_remain_valid(self):
        for count in [3, 6, 11]:
            with self.subTest(count=count):
                self.assertEqual(len(self.run_result(self.fixture(count))['visuals']), count)

    def test_all_frontend_profiles_pass_real_helper_validation(self):
        source = (ROOT / 'generation.js').read_text(encoding='utf-8')
        profiles = re.findall(r'(\w+):\{label:.*?images:(\d+)\}', source.split('const SG_CURRENT_PROFILE_KEYS')[0])
        self.assertEqual(len(profiles), 6)
        for name, body_count in profiles:
            with self.subTest(profile=name):
                count = int(body_count) + 1
                self.assertEqual(len(self.run_result(self.fixture(count))['visuals']), count)

    def test_invalid_counts_rejected(self):
        for count in [4, 8, 9, 10]:
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, 'число визуальных мест'):
                self.run_result(self.fixture(count))

    def test_non_array_rejected(self):
        result = self.fixture(5)
        result['visuals'] = None
        with self.assertRaisesRegex(ValueError, 'число визуальных мест'):
            self.run_result(result)

    def test_execution_mode_preserved(self):
        result = self.run_result(self.fixture(5))
        self.assertEqual(result['execution'], {'model': 'gpt-6.1-sol', 'reasoningEffort': 'high', 'authMode': 'chatgpt'})

    def test_other_operations_do_not_need_visuals(self):
        for operation, result in [('edit', {'html': '<p>Revision</p>', 'seo': self.fixture(5)['seo']}),
                                  ('revision', {'html': '<p>Revision</p>'}),
                                  ('audit', {'criteria': [{}] * 23})]:
            with self.subTest(operation=operation):
                self.assertIn('execution', self.run_result(result, operation))

    def test_missing_html_and_seo_still_rejected(self):
        for key in ['html', 'seo']:
            result = self.fixture(5)
            del result[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_result(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
