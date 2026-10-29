#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exercise the actual HTTP handler on an isolated ephemeral loopback port."""
import http.client,json,sys,threading,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'helper'))
import alfaprom_helper as helper

class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=helper.ThreadingHTTPServer(('127.0.0.1',0),helper.Handler)
        cls.port=cls.server.server_port
        cls.host='127.0.0.1:'+str(cls.port);cls.origin='http://'+cls.host
        cls.patches=[patch.object(helper,'HOST',cls.host),patch.object(helper,'ORIGIN',cls.origin),patch.object(helper,'SESSION','fixture-session-180')]
        for p in cls.patches:p.start()
        cls.worker=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.worker.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.worker.join()
        for p in cls.patches:p.stop()
    def request(self,path,body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        h={'Host':self.host,'Origin':self.origin,'X-Alfaprom-Session':'fixture-session-180','Content-Type':'application/json'};h.update(headers or {})
        conn.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,h)
        response=conn.getresponse();data=response.read();status=response.status;conn.close();return status,data
    def test_health_and_script(self):
        status,data=self.request('/health');self.assertEqual(status,200);self.assertEqual(json.loads(data)['version'],10)
        status,data=self.request('/quality-autofix.js?v=1.8.0');self.assertEqual(status,200);self.assertIn(b'QA_STANDARD=2',data)
    def test_patch_dispatches_exact_operation(self):
        with patch.object(helper,'execute_task',return_value={'version':2,'replacements':[]}) as execute:
            status,data=self.request('/patch',{'jobId':'fixture-patch-180','prompt':'x'*120})
        self.assertEqual(status,200);self.assertEqual(execute.call_args.args[2],'patch');self.assertEqual(json.loads(data)['authMode'],'chatgpt')
    def test_focused_dispatches_actual_attachments_and_links(self):
        assets=['a'*32];links=['https://henkelman.com/en/support']
        with patch.object(helper,'execute_task',return_value={'version':2,'criteria':[]}) as execute:
            status,_=self.request('/focused_audit',{'jobId':'fixture-audit-180','prompt':'x'*120,'assetIds':assets,'articleLinks':links})
        self.assertEqual(status,200);self.assertEqual(execute.call_args.args[2:],('focused_audit',assets,links))
    def test_link_recheck_does_not_invoke_gpt(self):
        with patch.object(helper,'verify_links',return_value=[{'url':'https://alfaprom.org/','ok':True}]) as verify,patch.object(helper,'execute_task') as execute:
            status,data=self.request('/links',{'jobId':'fixture-links-180','articleLinks':['https://alfaprom.org/']})
        self.assertEqual(status,200);self.assertTrue(json.loads(data)['linkChecks'][0]['ok']);verify.assert_called_once();execute.assert_not_called()

    def test_unknown_origin_blocked_before_inference(self):
        with patch.object(helper,'execute_task') as execute:
            status,_=self.request('/patch',{'jobId':'fixture-patch-180','prompt':'x'*120},{'Origin':'https://evil.example'})
        self.assertEqual(status,403);execute.assert_not_called()
    def test_missing_or_wrong_session_blocked(self):
        status,_=self.request('/patch',{'jobId':'fixture-patch-180','prompt':'x'*120},{'X-Alfaprom-Session':'wrong'});self.assertEqual(status,403)
    def test_host_rebinding_blocked(self):
        status,_=self.request('/health',headers={'Host':'evil.example'});self.assertEqual(status,403)
    def test_unknown_route_and_invalid_prompt(self):
        self.assertEqual(self.request('/unknown',{'jobId':'fixture-patch-180'})[0],404)
        with patch.object(helper,'execute_task') as execute:
            self.assertEqual(self.request('/patch',{'jobId':'fixture-patch-180','prompt':'short'})[0],400)
        execute.assert_not_called()
    def test_inference_cannot_run_concurrently(self):
        helper.JOB_LOCK.acquire()
        try:
            with patch.object(helper,'execute_task') as execute:
                status,_=self.request('/patch',{'jobId':'fixture-patch-180','prompt':'x'*120})
            self.assertEqual(status,409);execute.assert_not_called()
        finally:helper.JOB_LOCK.release()

if __name__=='__main__':unittest.main(verbosity=2)
