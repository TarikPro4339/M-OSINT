import base64
import hashlib
import threading
from types import SimpleNamespace
import unittest

from mosint import AUTHOR, VERSION
from mosint.catalog import catalog, FEATURE_COUNT
from mosint.server import Handler
from mosint.tools import local_tool, file_tool


class ExtraToolTests(unittest.TestCase):
    def test_catalog_contains_exactly_five_new_ready_local_tools(self):
        self.assertEqual(FEATURE_COUNT,111)
        self.assertEqual([f['id'] for f in catalog()[105:110]],list(range(106,111)))
        for feature in catalog()[105:110]:
            self.assertEqual(feature['status'],'functional')
            self.assertTrue(feature['runnable'])
            self.assertFalse(feature['network'])
        self.assertEqual(catalog()[108]['kind'],'file')

    def test_url_removes_tracking_but_keeps_other_values_duplicates_and_fragment(self):
        result=local_tool(106,'https://example.com/x?id=1&id=2&empty=&UTM_source=mail&fbclid=x#section',{})
        self.assertEqual(result['clean_url'],'https://example.com/x?id=1&id=2&empty=#section')
        self.assertEqual(result['removed_parameters'],['UTM_source','fbclid'])
        untouched='https://example.com/?a=hello%20world'
        self.assertEqual(local_tool(106,untouched,{})['clean_url'],untouched)

    def test_bad_urls_are_rejected_without_a_request(self):
        for value in ['example.com','javascript:alert(1)','https://user:password@example.com','https://example.com/a b','https://example.com\\x','https://example.com:0']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                local_tool(106,value,{})

    def test_ioc_comparison_is_unique_trimmed_and_case_sensitive(self):
        result=local_tool(107,' example.com\nA\nA\n---\nexample.com\na\nB',{})
        self.assertEqual(result['common'],['example.com'])
        self.assertEqual(result['only_first'],['A'])
        self.assertEqual(result['only_second'],['B','a'])
        self.assertEqual(result['first_unique_count'],2)

    def test_section_and_list_limits_are_enforced(self):
        for n in (107,110):
            with self.assertRaises(ValueError):local_tool(n,'no delimiter',{})
        with self.assertRaises(ValueError):local_tool(107,'x\n'*2001+'---\nx',{})
        with self.assertRaises(ValueError):local_tool(110,'x\n'*1001+'---\nx',{})

    def test_masker_preserves_surrounding_text_and_whitespace(self):
        text='  mail: alice@example.com; ikinci: b+tag@example.org\n'
        result=local_tool(108,text,{})
        self.assertEqual(result['masked_text'],'  mail: a***@example.com; ikinci: b***@example.org\n')
        self.assertEqual(result['masked_count'],2)
        self.assertEqual(local_tool(108,'E-posta yok',{})['masked_count'],0)

    def test_file_hash_matching_and_mismatch(self):
        payload={'file':base64.b64encode(b'hello').decode(),'text':hashlib.sha256(b'hello').hexdigest().upper()}
        self.assertTrue(file_tool(109,payload)['matches'])
        self.assertFalse(file_tool(109,{**payload,'text':'0'*64})['matches'])

    def test_file_hash_rejects_invalid_expected_digest(self):
        for digest in ['', 'x'*64,'a'*63,'a'*65]:
            with self.assertRaises(ValueError):
                file_tool(109,{'file':base64.b64encode(b'hello').decode(),'text':digest})

    def test_diff_reports_change_and_equal_lines(self):
        result=local_tool(110,'same\nold\n---\nsame\nnew',{})
        self.assertFalse(result['identical_lines'])
        self.assertIn('-old',result['unified_diff'])
        self.assertIn('+new',result['unified_diff'])
        self.assertTrue(local_tool(110,'a\r\n---\r\na',{})['identical_lines'])

    def test_all_new_tools_pass_api_dispatch(self):
        handler=object.__new__(Handler)
        handler.server=SimpleNamespace(keys={},key_lock=threading.Lock())
        examples={106:'https://example.com/?utm_source=mail',107:'a\n---\nb',108:'  a@example.com\n',
                  109:hashlib.sha256(b'hello').hexdigest(),110:'  a\n---\n  b'}
        for n,text in examples.items():
            payload={'id':n,'text':text}
            if n==109:payload['file']=base64.b64encode(b'hello').decode()
            result=handler.run_tool(payload)
            self.assertEqual(result['feature_id'],n)
            self.assertEqual(result['status'],'functional')
            if n==108:self.assertTrue(result['result']['masked_text'].startswith('  '))

    def test_author_and_version_preferences(self):
        self.assertEqual(AUTHOR,'TarikPro43391')
        self.assertEqual(VERSION,'1.0.0')


if __name__=='__main__':unittest.main()
