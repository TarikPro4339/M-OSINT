"""HTTP parser/handler tests without sockets; does not replace live HTTP QA."""
import collections
import io
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_server as socket_contract
from mosint import VERSION
from mosint.server import Handler


class MemorySocket:
    def __init__(self, raw):
        self.input=io.BytesIO(raw)
        self.output=io.BytesIO()
    def makefile(self,mode,*args):
        return self.input
    def settimeout(self,value):
        pass
    def sendall(self,data):
        self.output.write(data)


class MemoryHTTPTests(socket_contract.ServerTests):
    @classmethod
    def setUpClass(cls):
        cls.port=8765
        cls.server=SimpleNamespace(origin='http://127.0.0.1:8765',token='memory-test-session',keys={},
                                  key_lock=threading.Lock(),jobs=threading.BoundedSemaphore(2),
                                  rate_lock=threading.Lock(),times=collections.deque())

    @classmethod
    def tearDownClass(cls):
        pass

    def request(self,path='/api/run',payload=None,**overrides):
        headers={'Host':'127.0.0.1:8765','Origin':self.server.origin,
                 'X-MOSINT-Token':self.server.token,'Content-Type':'application/json'}
        headers.update(overrides)
        body=json.dumps(payload).encode() if payload is not None else b''
        if body:headers.setdefault('Content-Length',str(len(body)))
        method='POST' if payload is not None else 'GET'
        request=(method+' '+path+' HTTP/1.1\r\n'+''.join(k+': '+v+'\r\n' for k,v in headers.items())+'\r\n').encode('latin1')+body
        sock=MemorySocket(request)
        Handler(sock,('127.0.0.1',10000),self.server)
        header,body=sock.output.getvalue().split(b'\r\n\r\n',1)
        lines=header.decode('latin1').split('\r\n')
        status=int(lines[0].split()[1])
        rh=dict(line.split(': ',1) for line in lines[1:])
        return status,json.loads(body) if 'application/json' in rh.get('Content-Type','') else body,rh

    def test_non_ascii_request_token_returns_json_403(self):
        status,result,_=self.request(payload={'id':11,'text':'10.0.0.0/24'},**{'X-MOSINT-Token':'é'})
        self.assertEqual(status,403)
        self.assertIn('error',result)

    def test_version_matches_bootstrap_health_and_ui(self):
        self.assertEqual(self.request('/api/bootstrap')[1]['version'],VERSION)
        self.assertEqual(self.request('/api/health')[1]['version'],VERSION)
        html=self.request('/')[1].decode('utf-8')
        self.assertEqual(html.count('data-app-version>v'+VERSION),2)
        self.assertNotIn('1.0.1',html)

    def test_active_authorization_must_be_explicit_boolean(self):
        for value in ['false','true',1]:
            with patch('mosint.tools.public_addresses') as resolve:
                status,result,_=self.request(payload={'id':5,'text':'example.com','network_consent':True,'authorized':value})
                self.assertEqual(status,400)
                resolve.assert_not_called()


if __name__=='__main__':unittest.main()
