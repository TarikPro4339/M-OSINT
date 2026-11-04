import collections
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_http_memory as memory_http
from mosint.catalog import catalog
from mosint.hibp import email_breaches

KEY='a'*32
ACCOUNT='account-exists@hibp-integration-tests.com'
BREACH={'Name':'ExampleBreach','Title':'Example breach','Domain':'example.com','BreachDate':'2020-01-01',
        'DataClasses':['Email addresses','Passwords'],'IsVerified':True,
        'Description':'<script>not included in the result</script>'}


def response(code,body=None,headers=None):
    return {'status':code,'body':json.dumps(body).encode() if body is not None else b'', 'headers':headers or {}}


class HIBPTests(unittest.TestCase):
    def fixture(self):
        api=SimpleNamespace(port=8765,server=SimpleNamespace(origin='http://127.0.0.1:8765',token='test-session',keys={},
            key_lock=threading.Lock(),jobs=threading.BoundedSemaphore(2),rate_lock=threading.Lock(),times=collections.deque()))
        api.request=lambda path='/api/run',payload=None,**kw:memory_http.MemoryHTTPTests.request(api,path,payload,**kw)
        return api

    def test_direct_request_escapes_address_and_uses_key_header(self):
        with patch('mosint.hibp.fetch',return_value=response(200,[BREACH])) as fetch:
            result=email_breaches('first+tag@example.com',KEY)
        args=fetch.call_args
        self.assertIn('/breachedaccount/first%2Btag%40example.com?',args.args[0])
        self.assertIn('includeUnverified=false',args.args[0])
        self.assertNotIn(KEY,args.args[0])
        self.assertEqual(args.kwargs['headers']['hibp-api-key'],KEY)
        self.assertEqual(args.kwargs['redirects'],0)
        self.assertTrue(result['found'])
        self.assertEqual(result['breach_count'],1)
        self.assertNotIn('Description',json.dumps(result))
        self.assertNotIn(KEY,json.dumps(result))

    def test_404_is_scoped_no_record_with_caveat(self):
        with patch('mosint.hibp.fetch',return_value=response(404)):
            result=email_breaches(ACCOUNT,KEY)
        self.assertFalse(result['found'])
        self.assertEqual(result['breaches'],[])
        self.assertIn('kanıtlamaz',result['note'])

    def test_401_403_429_500_never_become_no_breach(self):
        for code in [401,403,429,500]:
            with self.subTest(code=code),patch('mosint.hibp.fetch',return_value=response(code,{'secret':KEY},{'retry-after':'60'})):
                with self.assertRaisesRegex(ValueError,str(code)) as error:
                    email_breaches(ACCOUNT,KEY)
                self.assertNotIn(KEY,str(error.exception))

    def test_rate_limit_uses_retry_after_without_retrying(self):
        with patch('mosint.hibp.fetch',return_value=response(429,headers={'retry-after':'60'})) as fetch:
            with self.assertRaisesRegex(ValueError,'60 saniye'):
                email_breaches(ACCOUNT,KEY)
        fetch.assert_called_once()

    def test_malformed_success_is_unknown_not_clean(self):
        for body in [[],{},[{}],[{'Name':'X','DataClasses':'bad'}],[{'Name':'X','IsVerified':'true'}]]:
            with self.subTest(body=body),patch('mosint.hibp.fetch',return_value=response(200,body)),self.assertRaises(ValueError):
                email_breaches(ACCOUNT,KEY)
        with patch('mosint.hibp.fetch',return_value={'status':200,'headers':{},'body':b'not json'}),self.assertRaises(ValueError):
            email_breaches(ACCOUNT,KEY)

    def test_bad_email_or_key_never_contacts_hibp(self):
        for email,key in [('invalid',KEY),('a..b@example.com',KEY),(ACCOUNT,''),(ACCOUNT,'z'*32),(ACCOUNT,'a'*31)]:
            with patch('mosint.hibp.fetch') as fetch,self.assertRaises(ValueError):
                try:email_breaches(email,key)
                finally:fetch.assert_not_called()

    def test_catalog_requires_only_key_and_keeps_ip_keyless(self):
        self.assertFalse(catalog()[49]['runnable'])
        rows=catalog({'hibp':KEY})
        self.assertTrue(rows[49]['runnable'])
        self.assertTrue(rows[49]['network'])
        self.assertEqual(rows[49]['status'],'functional')
        self.assertTrue(rows[0]['runnable'])

    def test_keys_preserved_independently_and_never_echoed(self):
        api=self.fixture()
        self.assertEqual(api.request('/api/settings',{'ipinfo':'test-ipinfo'})[0],200)
        status,body,_=api.request('/api/settings',{'hibp':KEY})
        self.assertEqual(status,200)
        self.assertTrue(body['configured']['hibp'])
        self.assertTrue(body['configured']['ipinfo'])
        self.assertNotIn(KEY,json.dumps(body))
        self.assertNotIn(KEY,json.dumps(api.request('/api/catalog')[1]))
        api.request('/api/settings',{'ipinfo':''})
        self.assertEqual(api.server.keys,{'hibp':KEY})
        api.request('/api/settings',{'ipinfo':'other'})
        api.request('/api/settings',{'hibp':''})
        self.assertEqual(api.server.keys,{'ipinfo':'other'})

    def test_invalid_key_update_is_atomic(self):
        api=self.fixture()
        api.request('/api/settings',{'ipinfo':'original'})
        self.assertEqual(api.request('/api/settings',{'ipinfo':'changed','hibp':'invalid'})[0],400)
        self.assertEqual(api.server.keys,{'ipinfo':'original'})

    def test_api_needs_key_and_network_consent_before_query(self):
        api=self.fixture()
        with patch('mosint.hibp.fetch') as fetch:
            self.assertEqual(api.request(payload={'id':50,'text':ACCOUNT,'network_consent':True})[0],400)
            api.request('/api/settings',{'hibp':KEY})
            self.assertEqual(api.request(payload={'id':50,'text':ACCOUNT})[0],400)
            fetch.assert_not_called()

    def test_api_success_and_404(self):
        api=self.fixture()
        api.request('/api/settings',{'hibp':KEY})
        for code,body,found in [(200,[BREACH],True),(404,None,False)]:
            with patch('mosint.hibp.fetch',return_value=response(code,body)):
                status,result,_=api.request(payload={'id':50,'text':ACCOUNT,'network_consent':True})
                self.assertEqual(status,200)
                self.assertEqual(result['result']['found'],found)
                self.assertNotIn(KEY,json.dumps(result))

    def test_api_provider_errors_do_not_return_a_result(self):
        api=self.fixture()
        api.request('/api/settings',{'hibp':KEY})
        with patch('mosint.hibp.fetch',return_value=response(429,headers={'retry-after':'5'})):
            status,result,_=api.request(payload={'id':50,'text':ACCOUNT,'network_consent':True})
        self.assertEqual(status,400)
        self.assertIn('429',result['error'])
        self.assertNotIn('result',result)


if __name__=='__main__':unittest.main()
