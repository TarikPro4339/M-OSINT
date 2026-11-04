import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit
import test_hibp as hibp_tests
from mosint.catalog import catalog
from mosint.oathnet import breach_summary

KEY='test-oathnet-key'
ACCOUNT='user@example.com'


def response(rows=None,total=None,more=False,status=200,success=True):
    rows=[] if rows is None else rows
    body={'success':success,'data':{'items':rows,'meta':{'total':len(rows) if total is None else total,'has_more':more},'next_cursor':'not-exported'}}
    return {'status':status,'body':json.dumps(body).encode(),'headers':{}}


class OathNetTests(unittest.TestCase):
    def api(self):
        return hibp_tests.HIBPTests().fixture()

    def test_exact_email_header_and_no_redirects(self):
        with patch('mosint.oathnet.fetch',return_value=response()) as fetch:
            breach_summary('first+tag@example.com',KEY)
        args=fetch.call_args
        query=parse_qs(urlsplit(args.args[0]).query)
        self.assertEqual(query,{'email[]':['first+tag@example.com'],'wildcard':['false']})
        self.assertNotIn(KEY,args.args[0])
        self.assertEqual(args.kwargs['headers']['x-api-key'],KEY)
        self.assertEqual(args.kwargs['redirects'],0)

    def test_only_metadata_is_returned(self):
        rows=[{'email':ACCOUNT,'dbname':'example_source','password':'do-not-return','token':'do-not-return',
               'password_hash':'do-not-return','phone':'do-not-return','other':{'cookie':'do-not-return'}},
              {'email':ACCOUNT.upper(),'dbname':'example_source'}]
        with patch('mosint.oathnet.fetch',return_value=response(rows,total=10,more=True)):
            result=breach_summary(ACCOUNT,KEY)
        self.assertTrue(result['found'])
        self.assertEqual(result['matching_rows_in_page'],2)
        self.assertEqual(result['total_rows_reported'],10)
        self.assertTrue(result['has_more'])
        self.assertEqual(result['breach_sources'],[{'database':'example_source','matching_rows_in_page':2}])
        self.assertNotIn('do-not-return',json.dumps(result))
        self.assertNotIn('not-exported',json.dumps(result))

    def test_documented_empty_success_is_scoped_no_result(self):
        with patch('mosint.oathnet.fetch',return_value=response()):
            result=breach_summary(ACCOUNT,KEY)
        self.assertFalse(result['found'])
        self.assertIn('kanıtı değildir',result['note'])

    def test_http_errors_never_become_empty_success(self):
        for code in [401,403,404,429,500]:
            with patch('mosint.oathnet.fetch',return_value=response(status=code)),self.assertRaisesRegex(ValueError,str(code)):
                breach_summary(ACCOUNT,KEY)

    def test_unexpected_email_or_source_is_rejected(self):
        for row in [{'email':'someone-else@example.com','dbname':'source'}, {'email':ACCOUNT},'bad row']:
            with patch('mosint.oathnet.fetch',return_value=response([row])),self.assertRaises(ValueError):
                breach_summary(ACCOUNT,KEY)

    def test_bad_envelope_or_pagination_is_not_clean(self):
        bad=[response(success=False),response(total=10),response(more=True),response(total=True),
             {'status':200,'headers':{},'body':b'bad json'},
             {'status':200,'headers':{},'body':b'{"success":true,"data":{}}'}]
        for body in bad:
            with patch('mosint.oathnet.fetch',return_value=body),self.assertRaises(ValueError):
                breach_summary(ACCOUNT,KEY)

    def test_invalid_key_or_email_makes_no_request(self):
        for email,key in [('bad',KEY),(ACCOUNT,''),(ACCOUNT,'with space'),(ACCOUNT,'x'*257),('a..b@example.com',KEY)]:
            with patch('mosint.oathnet.fetch') as fetch,self.assertRaises(ValueError):
                try:breach_summary(email,key)
                finally:fetch.assert_not_called()

    def test_catalog_marks_key_requirement_and_partial_scope(self):
        self.assertFalse(catalog()[110]['runnable'])
        feature=catalog({'oathnet':KEY})[110]
        self.assertTrue(feature['runnable'])
        self.assertTrue(feature['network'])
        self.assertEqual(feature['status'],'partial')

    def test_three_provider_keys_are_independent(self):
        api=self.api()
        api.request('/api/settings',{'hibp':'a'*32,'ipinfo':'ip-key'})
        status,body,_=api.request('/api/settings',{'oathnet':KEY})
        self.assertEqual(status,200)
        self.assertEqual(body['configured'],{'hibp':True,'ipinfo':True,'oathnet':True})
        self.assertNotIn(KEY,json.dumps(body))
        self.assertNotIn(KEY,json.dumps(api.request('/api/catalog')[1]))
        api.request('/api/settings',{'oathnet':''})
        self.assertEqual(api.server.keys,{'hibp':'a'*32,'ipinfo':'ip-key'})

    def test_api_requires_key_and_explicit_network_consent(self):
        api=self.api()
        with patch('mosint.oathnet.fetch') as fetch:
            self.assertEqual(api.request(payload={'id':111,'text':ACCOUNT,'network_consent':True})[0],400)
            api.request('/api/settings',{'oathnet':KEY})
            self.assertEqual(api.request(payload={'id':111,'text':ACCOUNT})[0],400)
            fetch.assert_not_called()

    def test_api_success_exports_only_summary(self):
        api=self.api()
        api.request('/api/settings',{'oathnet':KEY})
        with patch('mosint.oathnet.fetch',return_value=response([{'email':ACCOUNT,'dbname':'source','password':'hidden-secret'}])):
            status,result,_=api.request(payload={'id':111,'text':ACCOUNT,'network_consent':True})
        self.assertEqual(status,200)
        self.assertEqual(result['feature_id'],111)
        self.assertEqual(result['status'],'partial')
        self.assertNotIn('hidden-secret',json.dumps(result))


if __name__=='__main__':unittest.main()
