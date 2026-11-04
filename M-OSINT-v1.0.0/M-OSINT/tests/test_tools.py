import base64
import hashlib
import io
import ipaddress
import unittest
from unittest.mock import patch, Mock
import zipfile
from mosint.tools import local_tool, file_tool, codec_tool, b58encode, b58decode, mmh3, iocs, safe_zip
from mosint.catalog import catalog
from mosint.profiles import PROFILE_TEMPLATES
from mosint import network


class LocalTests(unittest.TestCase):
    def run_tool(self,n,text,**data):
        return local_tool(n,text,data)

    def test_catalog_complete_and_unique(self):
        rows=catalog()
        self.assertEqual([r['id'] for r in rows],list(range(1,112)))
        self.assertTrue(all(r['note'] for r in rows))
        self.assertEqual(len(PROFILE_TEMPLATES),55)

    def test_cidr_ipv4_ipv6_edge_masks(self):
        self.assertEqual(self.run_tool(11,'192.168.1.5/24')['usable_addresses'],254)
        self.assertEqual(self.run_tool(11,'10.0.0.1/31')['usable_addresses'],2)
        self.assertEqual(self.run_tool(11,'10.0.0.1/32')['usable_addresses'],1)
        self.assertEqual(self.run_tool(11,'2001:db8::/64')['usable_addresses'],2**64-1)
        self.assertEqual(self.run_tool(11,'2001:db8::/128')['first_host'],'2001:db8::')

    def test_cidr_zero_based_ipv6_preserves_address_family(self):
        for cidr,first,last in [('::/128','::','::'),('::/127','::','::1'),('::/126','::1','::3')]:
            result=self.run_tool(11,cidr)
            self.assertEqual(result['first_host'],first)
            self.assertEqual(result['last_host'],last)

    def test_fixed_version_policy(self):
        from mosint import VERSION
        self.assertEqual(VERSION,'1.0.0')
        self.assertIn('M-OSINT/'+VERSION,network.UA)

    def test_ip_parsing_and_mapped(self):
        self.assertEqual(ipaddress.ip_address(self.run_tool(12,'192.0.2.1')['ipv4_mapped']),ipaddress.IPv6Address('::ffff:192.0.2.1'))
        self.assertEqual(self.run_tool(12,'2001:db8::1')['version'],6)

    def test_snowflake_known_vector(self):
        self.assertEqual(self.run_tool(35,'175928847299117063')['created_utc'],'2016-04-30T11:18:25.796000+00:00')
        with self.assertRaises(ValueError):self.run_tool(35,str(2**64))

    def test_steam_round_trip(self):
        value=self.run_tool(37,'76561197960265729')
        self.assertEqual(value['Steam3'],'[U:1:1]')
        self.assertEqual(self.run_tool(37,value['Steam2'])['Steam64'],'76561197960265729')
        self.assertEqual(self.run_tool(37,value['Steam3'])['Steam64'],'76561197960265729')

    def test_username_is_link_generation(self):
        value=self.run_tool(31,'example')
        self.assertEqual(len(value['links']),55)
        self.assertNotIn('found',value)
        with self.assertRaises(ValueError):self.run_tool(31,'x/y')

    def test_generators(self):
        self.assertIn('ada.lovelace',self.run_tool(40,'Ada, Lovelace, 1815')['candidates'])
        self.assertIn('ada.lovelace@example.com',self.run_tool(49,'Ada, Lovelace, example.com')['candidates'])
        self.assertEqual(len(self.run_tool(89,'example.com')['queries']),4)
        self.assertEqual(self.run_tool(13,'192.0.2.0/24')['Shodan'],'net:192.0.2.0/24')

    def test_mail_syntax_does_not_claim_delivery(self):
        self.assertTrue(self.run_tool(46,'test@example.com')['syntax_valid'])
        for value in ['a..b@example.com','x@a..com','a@','a b@example.com']:
            self.assertFalse(self.run_tool(46,value)['syntax_valid'])
        self.assertFalse(self.run_tool(48,'x@example.com')['in_sample_list'])

    def test_mail_headers_parse_received_and_auth(self):
        value=self.run_tool(51,'From: a@example.com\nReceived: from mx [203.0.113.10]\nAuthentication-Results: example.com; spf=pass\n\n')
        self.assertEqual(value['received_ip_candidates'],['203.0.113.10'])
        self.assertEqual(len(value['authentication_results']),1)

    def test_e164_and_no_account_claim(self):
        self.assertTrue(self.run_tool(53,'+905551234567')['e164_syntax'])
        with self.assertRaises(ValueError):self.run_tool(53,'05551234567')
        self.assertEqual(len(self.run_tool(57,'+905551234567')['links']),2)

    def test_codecs_preserve_unicode_and_whitespace(self):
        text='  Merhaba dünya\n'
        for kind in ['base64','base32','base58','hex','binary','url','html']:
            with self.subTest(kind=kind):
                encoded=codec_tool(text,kind+'_encode')['output']
                self.assertEqual(codec_tool(encoded,kind+'_decode')['output'],text)
        self.assertEqual(b58decode(b58encode(b'\0\0abc')),b'\0\0abc')

    def test_invalid_codecs_fail(self):
        for kind,text in [('base64','%%%'),('base32','!'),('base58','0OIl'),('hex','zz'),('binary','2222')]:
            with self.subTest(kind=kind),self.assertRaises((ValueError,UnicodeError)):
                codec_tool(text,kind+'_decode')

    def test_base58_work_limits(self):
        with self.assertRaises(ValueError):b58encode(b'a'*4097)
        with self.assertRaises(ValueError):b58decode('a'*5601)

    def test_jwt_unverified(self):
        result=self.run_tool(80,'eyJhbGciOiJub25lIn0.eyJzdWIiOiJkZW1vIn0.')
        self.assertFalse(result['signature_verified'])
        self.assertEqual(result['payload']['sub'],'demo')

    def test_hash_candidates_ambiguous(self):
        self.assertEqual(self.run_tool(81,'a'*32)['candidates'],['MD5','NTLM'])

    def test_timestamp_explicit_units(self):
        self.assertEqual(self.run_tool(82,'0')['utc'],'1970-01-01T00:00:00+00:00')
        self.assertEqual(self.run_tool(82,'1000',mode='milliseconds')['unix_seconds'],1)
        self.assertEqual(self.run_tool(82,'2020-01-01T03:00:00+03:00')['utc'],'2020-01-01T00:00:00+00:00')
        with self.assertRaises(ValueError):self.run_tool(82,'2020-01-01')

    def test_iocs_validate_addresses(self):
        values=iocs('999.999.999.999 1.2.3.4 2001:db8::1 x@y.example https://example.com aa:bb:cc:dd:ee:ff')
        self.assertEqual(values['ip'],['1.2.3.4','2001:db8::1'])
        self.assertEqual(values['email'],['x@y.example'])

    def test_defang_round_trip(self):
        text='https://example.com/path'
        self.assertEqual(self.run_tool(84,self.run_tool(84,text)['output'],mode='refang')['output'],text)

    def test_morse_ascii_and_rot13(self):
        self.assertEqual(self.run_tool(85,'HELLO FRIEND')['output'],'.... . .-.. .-.. --- / ..-. .-. .. . -. -..')
        self.assertEqual(self.run_tool(85,'.... . .-.. .-.. ---',mode='morse_decode')['output'],'HELLO')
        self.assertEqual(self.run_tool(85,'65 66',mode='decimal_decode')['output'],'AB')
        self.assertEqual(self.run_tool(79,'hello')['ROT13'],'uryyb')

    def test_idna_wallet_and_magic(self):
        self.assertEqual(self.run_tool(86,'bücher.de')['ascii'],'xn--bcher-kva.de')
        self.assertTrue(self.run_tool(87,'1BoatSLRHtKNngkdXEeobR76b53LETtpyT')['checksum_verified'])
        self.assertFalse(self.run_tool(87,'1BoatSLRHtKNngkdXEeobR76b53LETtpyU')['checksum_verified'])
        self.assertFalse(self.run_tool(87,'0x'+'a'*40)['checksum_verified'])
        self.assertEqual(self.run_tool(88,'36383635366336633666')['output'],'hello')

    def test_html_parsing(self):
        self.assertEqual(len(self.run_tool(39,'<a href="https://linktr.ee/demo">link</a><script>bad()</script>')['links']),1)
        self.assertEqual(self.run_tool(42,'UC_x5XG1OV2P6uZZ5FSM9Ttw')['channel_ids'],['UC_x5XG1OV2P6uZZ5FSM9Ttw'])


class FileTests(unittest.TestCase):
    def f(self,n,raw):return file_tool(n,{'file':base64.b64encode(raw).decode()})

    def test_hashes_and_signatures(self):
        self.assertEqual(self.f(65,b'hello')['sha256'],hashlib.sha256(b'hello').hexdigest())
        self.assertEqual(self.f(66,b'%PDF-1.7')['signature_hint'],'PDF')
        self.assertEqual(self.f(66,b'other')['signature_hint'],'Unknown')

    def test_murmurhash_known_vectors(self):
        self.assertEqual(mmh3(b''),0)
        self.assertEqual(mmh3(b'hello'),613153351)
        self.assertEqual(mmh3(b'foo'),-156908512)
        self.assertEqual(self.f(28,b'hello')['murmurhash3_base64_signed'],mmh3(base64.encodebytes(b'hello')))

    def test_zip_list_no_extract_and_office(self):
        memory=io.BytesIO()
        with zipfile.ZipFile(memory,'w') as z:
            z.writestr('../../never-extracted.txt','hello')
            z.writestr('docProps/core.xml','<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>Example</dc:creator></cp:coreProperties>')
        self.assertEqual(self.f(74,memory.getvalue())['entries'][0]['name'],'../../never-extracted.txt')
        self.assertEqual(self.f(64,memory.getvalue())['core_properties']['creator'],'Example')

    def test_zip_bomb_ratio_rejected(self):
        memory=io.BytesIO()
        with zipfile.ZipFile(memory,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('bomb','a'*100000)
        with self.assertRaises(ValueError):self.f(74,memory.getvalue())

    def test_xml_entities_rejected(self):
        memory=io.BytesIO()
        with zipfile.ZipFile(memory,'w') as z:z.writestr('docProps/core.xml','<!DOCTYPE x [<!ENTITY y "test">]><x>&y;</x>')
        with self.assertRaises(ValueError):self.f(64,memory.getvalue())

    def test_jpeg_trailing_data_and_strings(self):
        self.assertEqual(self.f(72,b'\xff\xd8xx\xff\xd9ABC')['trailing_bytes'],3)
        self.assertIn('HELLO WORLD',self.f(67,b'\x00HELLO WORLD\x01')['ascii'])


class NetworkPolicyTests(unittest.TestCase):
    def answers(self,*addresses):
        return [(socket_family,1,6,'',(a,443)) for a in addresses for socket_family in [2]]

    def test_private_mixed_and_transition_dns_blocked(self):
        for addr in ['127.0.0.1','10.0.0.1','169.254.169.254','::1','::ffff:8.8.8.8','2002:0808:0808::1','192.0.2.1']:
            with self.subTest(addr=addr),patch.object(network.socket,'getaddrinfo',return_value=self.answers('8.8.8.8',addr)),self.assertRaises(ValueError):
                network.public_addresses('example.com')

    def test_public_dns_is_pinned(self):
        with patch.object(network.socket,'getaddrinfo',return_value=self.answers('8.8.8.8')):
            self.assertEqual(network.public_addresses('example.com'),('example.com',['8.8.8.8']))

    def test_url_forms_blocked(self):
        for value in ['file:///etc/passwd','https://x:y@example.com','https://@example.com','https://example.com:0','http://example.com:0','https://example.com:444','https://example.com/\r\nX:x','https://example.com\\@127.0.0.1']:
            with self.subTest(value=value),self.assertRaises(ValueError):network.parse_url(value)

    def test_onion_and_scope_blocked(self):
        for host in ['localhost.local','test.onion','fe80::1%eth0']:
            with self.assertRaises(ValueError):network.public_addresses(host)

    def test_dns_failure_has_readable_error(self):
        with patch.object(network.socket,'getaddrinfo',side_effect=network.socket.gaierror('unavailable')):
            with self.assertRaisesRegex(ValueError,'DNS'):
                network.public_addresses('example.com')

    def fake_connection(self,responses,calls):
        class Response:
            def __init__(self,status,headers,body):self.status=status;self.headers=headers;self.data=io.BytesIO(body)
            def getheaders(self):return self.headers.items()
            def read1(self,n):return self.data.read(n)
        class Connection:
            def __init__(self,host,port,address,secure):calls.append({'host':host,'address':address})
            def request(self,method,path,headers):calls[-1]['headers']=headers
            def getresponse(self):return Response(*responses.pop(0))
            def close(self):pass
        return Connection

    def test_redirect_revalidates_target(self):
        calls=[]
        conn=self.fake_connection([(302,{'location':'http://127.0.0.1/private'},b'')],calls)
        with patch.object(network,'PinnedHTTP',conn),patch.object(network,'public_addresses',side_effect=[('example.com',['8.8.8.8']),ValueError('private')]),self.assertRaises(ValueError):
            network.fetch('http://example.com')
        self.assertEqual(len(calls),1)

    def test_redirect_strips_credentials(self):
        calls=[]
        conn=self.fake_connection([(302,{'location':'https://other.example/'},b''),(200,{},b'OK')],calls)
        with patch.object(network,'PinnedHTTP',conn),patch.object(network,'public_addresses',side_effect=[('example.com',['8.8.8.8']),('other.example',['1.1.1.1'])]):
            self.assertEqual(network.fetch('https://example.com',headers={'Authorization':'Bearer test'})['body'],b'OK')
        self.assertIn('Authorization',calls[0]['headers'])
        self.assertNotIn('Authorization',calls[1]['headers'])
        self.assertEqual(calls[1]['address'],'1.1.1.1')

    def test_body_cap_and_downgrade(self):
        for responses in [[(200,{},b'12345')],[(302,{'location':'http://example.com'},b'')]]:
            conn=self.fake_connection(responses,[])
            with patch.object(network,'PinnedHTTP',conn),patch.object(network,'public_addresses',return_value=('example.com',['8.8.8.8'])),self.assertRaises(ValueError):
                network.fetch('https://example.com',max_body=4)

    def test_connection_tries_next_prevalidated_ip_and_is_bounded(self):
        raw=Mock()
        conn=network.PinnedHTTP('example.com',80,'2606:4700:4700::1111',False)
        conn.fallback_addresses=['1.1.1.1']
        with patch.object(network.socket,'create_connection',side_effect=[OSError('no IPv6 route'),raw]) as create:
            conn.connect()
        self.assertIs(conn.sock,raw)
        self.assertEqual(create.call_args_list[1].args[0],('1.1.1.1',80))
        conn=network.PinnedHTTP('example.com',80,'8.8.8.8',False)
        conn.fallback_addresses=['1.1.1.1']*10
        with patch.object(network.socket,'create_connection',side_effect=OSError('unreachable')) as create:
            with self.assertRaises(OSError):conn.connect()
            self.assertEqual(create.call_count,4)

    def test_bad_tls_certificate_is_not_bypassed_by_fallback(self):
        raw=Mock();context=Mock()
        context.wrap_socket.side_effect=network.ssl.SSLCertVerificationError('bad certificate')
        conn=network.PinnedHTTP('example.com',443,'8.8.8.8',True)
        conn.fallback_addresses=['1.1.1.1']
        with patch.object(network.socket,'create_connection',return_value=raw) as create,patch.object(network.ssl,'create_default_context',return_value=context):
            with self.assertRaises(network.ssl.SSLCertVerificationError):conn.connect()
        create.assert_called_once();raw.close.assert_called_once()

    def test_expired_connection_budget_makes_no_attempt(self):
        conn=network.PinnedHTTP('example.com',80,'8.8.8.8',False)
        conn.deadline=network.time.monotonic()-1
        with patch.object(network.socket,'create_connection') as create:
            with self.assertRaises(TimeoutError):conn.connect()
            create.assert_not_called()

    def test_truncated_http_responses_are_rejected_including_404(self):
        for status in (200,404):
            conn=self.fake_connection([(status,{'content-length':'5'},b'bad')],[])
            with patch.object(network,'PinnedHTTP',conn),patch.object(network,'public_addresses',return_value=('example.com',['8.8.8.8'])),self.assertRaisesRegex(ValueError,'eksik'):
                network.fetch('https://example.com')

if __name__=='__main__':unittest.main()
