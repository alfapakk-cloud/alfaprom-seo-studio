# -*- coding: utf-8 -*-
"""Bounded Codex and retrieval fixtures; no model calls, browser or actual network."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'helper'))
import alfaprom_helper as h
import quality_sources as s


class BatchesTests(unittest.TestCase):
    def simulate(self, operation, ids, timeout=False):
        captured = {}
        class Process:
            pid, returncode = 999999, 0
            def __init__(self, command, **options):
                captured['command'], captured['env'] = command, options['env']
                self.result = Path(command[command.index('--output-last-message') + 1])
                self.calls = 0
            def communicate(self, instruction=None, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    captured['timeout'], captured['instruction'] = timeout, instruction
                    if captured.get('fail'):
                        raise subprocess.TimeoutExpired('synthetic-codex', timeout)
                result = {'version': 2, 'fingerprint': 'fixture', 'criteria': [{'id': ids[0] if ids else 1, 'status': 'unverified', 'reason': 'Synthetic fixture without actual assessment.'}], 'replacements': [], 'sources': [], 'facts': [], 'visuals': []}
                self.result.write_text(json.dumps(result))
                return None, None
        captured['fail'] = timeout
        with patch.object(h, 'codex_binary', return_value='/synthetic/codex'), patch.object(h.subprocess, 'Popen', Process), patch.object(h.os, 'killpg') as kill, patch.object(h, 'verify_sources', side_effect=lambda data: {**data, 'sourceChecks': {'version': 1}}), patch.object(h, 'verify_links', return_value=[]):
            if timeout:
                with self.assertRaises(h.TaskTimeout) as raised:
                    h.execute_task('Synthetic scoped task.', 'synthetic-batch-182', operation, criteria_ids=ids)
                self.assertEqual(raised.exception.code, 'task_timeout'); kill.assert_called_once()
            else:
                h.execute_task('Synthetic scoped task.', 'synthetic-batch-182', operation, criteria_ids=ids)
        return captured

    def test_plain_text_patch_does_not_launch_web_research(self):
        c = self.simulate('patch', [6, 23])
        self.assertIn('web_search="disabled"', c['command']); self.assertEqual(c['timeout'], 300)
        self.assertIn('gpt-6.1-sol', c['command']); self.assertIn('model_reasoning_effort="high"', c['command'])
        self.assertIn('forced_login_method="chatgpt"', c['command']); self.assertNotIn('OPENAI_API_KEY', c['env'])

    def test_fact_group_keeps_live_primary_source_search(self):
        c = self.simulate('focused_audit', [3, 4, 22])
        self.assertIn('web_search="live"', c['command']); self.assertEqual(c['timeout'], 360)
        self.assertIn('максимум 3 точных запроса', c['instruction'])

    def test_full_audit_keeps_all_criteria_and_bounded_model_time(self):
        c = self.simulate('focused_audit', list(range(1, 24)))
        self.assertEqual(c['timeout'], 480); self.assertIn('web_search="live"', c['command'])

    def test_structured_timeout_can_trigger_only_the_matching_recovery(self):
        self.simulate('patch', [3, 4, 22], timeout=True)

    def test_malformed_scope_rejected_before_starting_codex(self):
        for ids in [[], [True], [0], [24], [3, 3], '3,4']:
            with patch.object(h, 'codex_binary') as binary, self.assertRaises(ValueError):
                h.execute_task('Fixture', 'synthetic-batch-182', 'patch', criteria_ids=ids)
            binary.assert_not_called()

    def test_retrieval_returns_by_wall_deadline_without_claiming_unfinished_success(self):
        release = threading.Event()
        def blocked(url):
            release.wait(0.5)
            return {'url': url, 'ok': True}
        start = time.monotonic()
        try:
            result = s.bounded_results(blocked, ['https://fixture.example/' + str(i) for i in range(8)], 0.025)
            self.assertLess(time.monotonic() - start, 0.25); self.assertEqual(result, {})
        finally:
            release.set()

    def test_deadline_sources_are_unverified_and_counted_honestly(self):
        data = {'criteria': [{'id': 3, 'status': 'pass', 'reason': 'Fixture'}], 'sources': [{'url': 'https://henkelman.com/en/support', 'title': 'Fixture document', 'quote': 'A sufficiently long synthetic quotation from a technical document.'}], 'facts': []}
        with patch.object(s, 'bounded_results', return_value={}):
            result = s.verify_sources(copy.deepcopy(data))
        self.assertEqual(result['criteria'][0]['status'], 'unverified'); self.assertEqual(result['sourceChecks']['checkedUrls'], 0)
        self.assertFalse(result['sources'][0]['verification']['verified'])

    def test_deadline_links_remain_unavailable_not_falsely_broken_or_passed(self):
        with patch.object(s, 'bounded_results', return_value={}):
            checks = s.verify_links(['https://alfaprom.org/'])
        self.assertEqual(checks[0]['ok'], False); self.assertEqual(checks[0]['kind'], 'unavailable')

    def test_cached_checks_keep_real_timestamp_and_explicit_retry_bypasses_them(self):
        url = 'https://henkelman.com/en/support'; doc = {'checkedAt': 'fixture-original-time', 'finalUrl': url, 'publicAllowed': True}
        with s.LINK_CACHE_LOCK: s.LINK_CACHE.clear()
        with patch.object(s, 'fetch_with_retry', return_value=doc) as fetch:
            first = s.verify_links([url], use_cache=True); second = s.verify_links([url], use_cache=True)
            self.assertEqual(fetch.call_count, 1); self.assertEqual(first, second)
            self.assertEqual(second[0]['checkedAt'], 'fixture-original-time')
            s.verify_links([url])
            self.assertEqual(fetch.call_count, 2)


if __name__ == '__main__': unittest.main(verbosity=2)
