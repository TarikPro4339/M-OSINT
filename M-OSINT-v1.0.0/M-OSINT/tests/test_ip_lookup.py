"""Keyless lookup regression tests, including API dispatch without sockets."""
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from mosint.catalog import catalog
from mosint.server import Handler
from mosint.tools import network_tool

SAMPLE={'ip':'8.8.8.8','success':True,'country':'United States','city':'Mountain View',
        'connection':{'asn':15169,'isp':'Google LLC','org':'Google LLC'}}


class KeylessIPTests(unittest.TestCase):
    def test_both_cards_enabled_without_keys(self):
        for feature in catalog()[:2]:
            self.assertTrue(feature['runnable'])
            self.assertIsNone(feature['requirement'])
            self.assertNotEqual(feature['status'],'integration')

    def test_keyless_request_has_no_authorization(self):
        for n in (1,2):
            with patch('mosint.tools.fetch_json',return_value=SAMPLE) as fetch:
                result=network_tool(n,'8.8.8.8',{}, {})
                args=fetch.call_args
                self.assertEqual(len(args.args),1)
                self.assertTrue(args.args[0].startswith('https://ipwho.is/8.8.8.8?fields='))
                self.assertFalse(args.kwargs)
                self.assertEqual(result['data']['connection']['asn'],15169)

    def test_provider_failure_is_not_a_result(self):
        for response in [{'success':False,'message':'Rate limit exceeded'},[],{},None]:
            with patch('mosint.tools.fetch_json',return_value=response),self.assertRaises(ValueError):
                network_tool(1,'8.8.8.8',{}, {})

    def test_mismatched_or_missing_ip_is_rejected(self):
        for response in [{**SAMPLE,'ip':'1.1.1.1'},{'success':True},{**SAMPLE,'ip':'bad'}]:
            with patch('mosint.tools.fetch_json',return_value=response),self.assertRaises(ValueError):
                network_tool(1,'8.8.8.8',{}, {})

    def test_missing_asn_data_is_not_reported_as_success(self):
        with patch('mosint.tools.fetch_json',return_value={**SAMPLE,'connection':{}}),self.assertRaises(ValueError):
            network_tool(2,'8.8.8.8',{}, {})

    def test_private_and_invalid_targets_never_contact_provider(self):
        for target in ['127.0.0.1','10.0.0.1','169.254.169.254','::1','not-an-ip']:
            with patch('mosint.tools.fetch_json') as fetch,self.assertRaises(ValueError):
                try:
                    network_tool(1,target,{}, {})
                finally:
                    fetch.assert_not_called()

    def test_optional_ipinfo_is_still_explicit(self):
        with patch('mosint.tools.fetch_json',return_value={'asn':'AS15169'}) as fetch:
            result=network_tool(2,'8.8.8.8',{}, {'ipinfo':'test-key'})
            self.assertEqual(fetch.call_args.args[1],{'Authorization':'Bearer test-key'})
            self.assertIn('IPinfo',result['source'])

    def handler(self):
        handler=object.__new__(Handler)
        handler.server=SimpleNamespace(keys={},key_lock=threading.Lock())
        return handler

    def test_api_dispatch_accepts_no_provider_key(self):
        for n in (1,2):
            with patch('mosint.tools.fetch_json',return_value=SAMPLE):
                result=self.handler().run_tool({'id':n,'text':'8.8.8.8','network_consent':True})
                self.assertEqual(result['feature_id'],n)
                self.assertIn('ipwho.is',result['result']['source'])

    def test_api_network_consent_remains_required(self):
        with patch('mosint.tools.fetch_json') as fetch,self.assertRaises(ValueError):
            try:
                self.handler().run_tool({'id':1,'text':'8.8.8.8'})
            finally:
                fetch.assert_not_called()


if __name__=='__main__':unittest.main()
