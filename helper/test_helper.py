import importlib.util
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('alfaprom_helper', Path(__file__).with_name('alfaprom_helper.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class HelperTests(unittest.TestCase):
    def test_api_credentials_are_not_inherited(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'CODEX_API_KEY': 'test', 'OPENAI_BASE_URL': 'test'}):
            result = helper.clean_environment()
        for key in ['OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL']:
            self.assertNotIn(key, result)

    def test_api_login_is_rejected(self):
        with patch.object(helper.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='Logged in using an API key', stderr='')):
            with self.assertRaises(ValueError):
                helper.require_chatgpt('codex', {})

    def test_missing_login_is_rejected(self):
        with patch.object(helper.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='', stderr='Not logged in')):
            with self.assertRaises(ValueError):
                helper.require_chatgpt('codex', {})

    def test_chatgpt_login_is_accepted(self):
        with patch.object(helper.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='', stderr='Logged in using ChatGPT')):
            helper.require_chatgpt('codex', {})

    def test_runner_requires_chatgpt_and_read_only(self):
        def fake_process(command, **kwargs):
            self.assertIn('--ignore-user-config', command)
            self.assertIn('--ephemeral', command)
            self.assertIn('forced_login_method="chatgpt"', command)
            self.assertIn('read-only', command)
            self.assertIn('features.shell_tool=false', command)
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', command)
            target = Path(command[command.index('--output-last-message') + 1])
            target.write_text('{"html":"<h2>Раздел</h2><p>Тестовый результат.</p>"}', encoding='utf-8')
            return SimpleNamespace(pid=999999, returncode=0, communicate=lambda *args, **kw: ('', ''))
        with patch.object(helper, 'codex_binary', return_value='codex'), patch.object(helper, 'require_chatgpt'), patch.object(helper.subprocess, 'Popen', side_effect=fake_process):
            self.assertIn('Тестовый результат', helper.execute_revision('Тест', 'test-job-001'))
        self.assertFalse(helper.ACTIVE)

    def test_quota_error_has_no_api_fallback(self):
        process = SimpleNamespace(pid=999999, returncode=1, communicate=lambda *args, **kw: ('', 'usage limit reached'))
        with patch.object(helper, 'codex_binary', return_value='codex'), patch.object(helper, 'require_chatgpt'), patch.object(helper.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'Лимит'):
                helper.execute_revision('Тест', 'test-job-002')
        self.assertFalse(helper.ACTIVE)


if __name__ == '__main__':
    unittest.main()
