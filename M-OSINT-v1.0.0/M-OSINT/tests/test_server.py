"""Actual loopback HTTP contract tests; no external service traffic."""
import http.client
import json
import threading
import unittest
from unittest.mock import patch
from mosint.server import Server, MAX_REQUEST


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=Server(0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.port=cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)

    def request(self,path='/api/run',payload=None,**overrides):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        headers={'Host':'127.0.0.1:'+str(self.port),'Origin':self.server.origin,'X-MOSINT-Token':self.server.token,'Content-Type':'application/json'}
        headers.update(overrides)
        raw=json.dumps(payload) if payload is not None else None
        conn.request('POST' if raw is not None else 'GET',path,raw,headers=headers)
        response=conn.getresponse();body=response.read();status=response.status;rh=dict(response.getheaders());conn.close()
        return status,json.loads(body) if 'application/json' in rh.get('Content-Type','') else body,rh

    def test_bootstrap_and_catalog(self):
        status,value,headers=self.request('/api/bootstrap')
        self.assertEqual(status,200);self.assertEqual(value['token'],self.server.token)
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(len(self.request('/api/catalog')[1]['features']),111)

    def test_host_origin_and_token_enforced(self):
        for overrides in [{'Host':'attacker.example'},{'Origin':'https://attacker.example'},{'X-MOSINT-Token':''}]:
            self.assertEqual(self.request(payload={'id':11,'text':'10.0.0.0/24'},**overrides)[0],403)

    def test_cross_site_bootstrap_blocked(self):
        self.assertEqual(self.request('/api/bootstrap',**{'Sec-Fetch-Site':'cross-site'})[0],403)

    def test_static_allowlist(self):
        self.assertEqual(self.request('/')[0],200)
        for path in ['/run.py','/../run.py','/%2e%2e/run.py','/mosint/server.py']:
            self.assertEqual(self.request(path)[0],404)

    def test_local_success_and_invalid_id(self):
        status,value,_=self.request(payload={'id':11,'text':'10.1.2.3/24'})
        self.assertEqual(status,200);self.assertEqual(value['result']['network'],'10.1.2.0/24')
        self.assertEqual(self.request(payload={'id':True,'text':''})[0],400)
        self.assertEqual(self.request(payload={'id':112})[0],400)

    def test_network_default_off_and_private_block(self):
        with patch('mosint.server.network_tool') as outbound:
            status,value,_=self.request(payload={'id':17,'text':'example.com'})
            self.assertEqual(status,400);outbound.assert_not_called()
        status,value,_=self.request(payload={'id':20,'text':'http://127.0.0.1','network_consent':True})
        self.assertEqual(status,400)

    def test_active_requires_authorization(self):
        self.assertEqual(self.request(payload={'id':5,'text':'example.com','network_consent':True})[0],400)

    def test_missing_integration_never_success(self):
        status,value,_=self.request(payload={'id':50,'text':'x@example.com'})
        self.assertEqual(status,400);self.assertNotIn('found',value)

    def test_keys_memory_only_no_echo(self):
        self.assertEqual(self.request('/api/settings',{'ipinfo':'example-test-token'})[0],200)
        self.assertNotIn('example-test-token',json.dumps(self.request('/api/catalog')[1]))
        self.assertTrue(self.request('/api/catalog')[1]['features'][1]['runnable'])
        self.assertEqual(self.request('/api/settings',{'ipinfo':''})[0],200)
        self.assertTrue(self.request('/api/catalog')[1]['features'][1]['runnable'])

    def test_batch_bounded_and_per_target_error(self):
        status,value,_=self.request('/api/batch',{'tool_id':11,'targets':['10.0.0.0/24','bad']})
        self.assertEqual(status,200);self.assertIn('error',value['result']['rows'][1])
        self.assertEqual(self.request('/api/batch',{'tool_id':11,'targets':['x']*21})[0],400)
        self.assertEqual(self.request('/api/batch',{'tool_id':17,'targets':['example.com']})[0],400)

    def test_body_limit_and_concurrency(self):
        self.assertEqual(self.request(payload={'id':11},**{'Content-Length':str(MAX_REQUEST+1)})[0],413)
        self.server.jobs.acquire();self.server.jobs.acquire()
        try:self.assertEqual(self.request(payload={'id':11,'text':'10.0.0.0/24'})[0],429)
        finally:self.server.jobs.release();self.server.jobs.release()

if __name__=='__main__':unittest.main()
