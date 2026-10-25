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
            self.assertIn('--json', command)
            self.assertIn('forced_login_method="chatgpt"', command)
            self.assertIn('read-only', command)
            self.assertIn('features.shell_tool=false', command)
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', command)
            target = Path(command[command.index('--output-last-message') + 1])
            target.write_text('{"html":"<h2>Раздел</h2><p>Тестовый результат.</p>"}', encoding='utf-8')
            return SimpleNamespace(pid=999999, returncode=0, communicate=lambda *args, **kw: ('', ''))
        with patch.object(helper, 'codex_binary', return_value='codex'), patch.object(helper, 'require_chatgpt', side_effect=ValueError('GUI config unavailable')), patch.object(helper.subprocess, 'Popen', side_effect=fake_process):
            self.assertIn('Тестовый результат', helper.execute_revision('Тест', 'test-job-001'))
        self.assertFalse(helper.ACTIVE)

    def test_quota_error_has_no_api_fallback(self):
        process = SimpleNamespace(pid=999999, returncode=1, communicate=lambda *args, **kw: ('', 'usage limit reached'))
        with patch.object(helper, 'codex_binary', return_value='codex'), patch.object(helper, 'require_chatgpt'), patch.object(helper.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'Лимит'):
                helper.execute_revision('Тест', 'test-job-002')
        self.assertFalse(helper.ACTIVE)

    def test_native_health_check_returns_only_service_metadata(self):
        calls = []
        fake = SimpleNamespace(path='/health', valid_host=lambda: True, send=lambda code, data: calls.append((code, data)))
        helper.Handler.do_GET(fake)
        self.assertEqual(calls, [(200, {'service': 'alfaprom-seo-helper', 'version': 5})])

    def test_progress_contains_no_article_or_account_data(self):
        helper.set_progress('progress-test', 'generating')
        data = helper.progress_snapshot('progress-test')
        self.assertEqual(set(data), {'stage', 'elapsed'})
        self.assertEqual(data['stage'], 'generating')
        self.assertGreaterEqual(data['elapsed'], 0)

    def test_unknown_job_is_only_connecting(self):
        self.assertEqual(helper.progress_snapshot('unknown-job'), {'stage': 'connecting', 'elapsed': 0})

    def test_event_stream_reports_stages_without_forwarding_text(self):
        import tempfile
        import threading
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'events.jsonl'
            path.write_text('{"type":"turn.started"}\n{"type":"item.completed","item":{"text":"PRIVATE"}}\n{"type":"turn.completed"}\n', encoding='utf-8')
            stop = threading.Event()
            def after_read(_):
                stop.set()
            with patch.object(stop, 'wait', side_effect=after_read):
                helper.watch_events(path, 'stream-test', stop)
            self.assertEqual(helper.progress_snapshot('stream-test')['stage'], 'validating')
            self.assertNotIn('PRIVATE', str(helper.PROGRESS))

    def test_cancel_before_generation_does_not_start_codex(self):
        helper.CANCELLED.add('cancelled-before-start')
        with patch.object(helper, 'codex_binary', return_value='codex'), patch.object(helper, 'require_chatgpt'), patch.object(helper.subprocess, 'Popen') as process:
            with self.assertRaisesRegex(ValueError, 'остановлена'):
                helper.execute_revision('test', 'cancelled-before-start')
            process.assert_not_called()

    def test_transfer_preserves_project_and_escapes_script_termination(self):
        import json
        project = {'currentId': 8, 'articles': [{'id': 8, 'content': '<p>Текст</p></script><script>bad()</script>'}]}
        page = helper.studio_page(project)
        payload = page.split('id="alfapromTransfer">', 1)[1].split('</script>', 1)[0]
        self.assertNotIn('<', payload)
        self.assertEqual(json.loads(payload), project)

    def test_transfer_rejects_non_project_payload(self):
        with self.assertRaises(ValueError):
            helper.studio_page({'content': 'not a project'})

    def test_native_shutdown_stops_active_generation(self):
        helper.ACTIVE['test-active-job'] = SimpleNamespace(pid=999999, poll=lambda: None)
        try:
            with patch.object(helper.os, 'killpg') as kill:
                helper.stop_children()
                kill.assert_called_once_with(999999, helper.signal.SIGTERM)
        finally:
            helper.ACTIVE.clear()


if __name__ == '__main__':
    unittest.main()
