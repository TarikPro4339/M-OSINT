"""Single-user loopback server, deliberately not an internet-facing service."""
import base64
import collections
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import re
import threading
import time

from . import VERSION
from .catalog import catalog, FILE_IDS, NETWORK_IDS, FEATURE_COUNT
from .tools import local_tool, network_tool, file_tool

STATIC=Path(__file__).resolve().parent.parent/'static'
MAX_REQUEST=12*1024*1024
BATCH_IDS={11,12,13,35,37,40,46,48,49,53,81,82,84,86,87,89,95}


class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=False
    request_queue_size=16

    def __init__(self, port=8765):
        super().__init__(('127.0.0.1',port),Handler)
        self.origin='http://127.0.0.1:'+str(self.server_address[1])
        self.token=secrets.token_urlsafe(32)
        self.keys={}
        self.key_lock=threading.Lock()
        self.jobs=threading.BoundedSemaphore(2)
        self.connections=threading.BoundedSemaphore(12)
        self.times=collections.deque()
        self.rate_lock=threading.Lock()

    def process_request(self, request, client_address):
        if not self.connections.acquire(blocking=False):
            try:
                request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request,client_address)
        except BaseException:
            self.connections.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request,client_address)
        finally:
            self.connections.release()

    def handle_error(self, request, client_address):
        # No request bodies, tokens, file contents or target URLs in logs.
        pass


class Handler(BaseHTTPRequestHandler):
    server_version='M-OSINT/'+VERSION
    sys_version=''

    def setup(self):
        super().setup()
        self.connection.settimeout(8)

    def log_message(self, fmt, *args):
        pass

    def valid_host(self):
        return self.headers.get_all('Host',[])==[self.server.origin.removeprefix('http://')]

    def send_data(self, value, status=200, content_type='application/json; charset=utf-8'):
        raw=json.dumps(value,ensure_ascii=False,default=str).encode('utf-8') if not isinstance(value,bytes) else value
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cross-Origin-Resource-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data: blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if not self.valid_host():
            return self.send_data({'error':'Geçersiz Host.'},403)
        if self.headers.get('Sec-Fetch-Site')=='cross-site':
            return self.send_data({'error':'Çapraz site isteği engellendi.'},403)
        if self.path=='/api/bootstrap':
            return self.send_data({'version':VERSION,'token':self.server.token,'network_default':False})
        if self.path=='/api/catalog':
            with self.server.key_lock:
                rows=catalog(self.server.keys)
            return self.send_data({'features':rows})
        if self.path=='/api/health':
            return self.send_data({'app':'M-OSINT','version':VERSION})
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),
               '/style.css':('style.css','text/css; charset=utf-8'),'/fsociety.ascii':('fsociety.ascii','text/plain; charset=utf-8')}
        if self.path not in files:
            return self.send_data({'error':'Bulunamadı.'},404)
        name,mime=files[self.path]
        return self.send_data((STATIC/name).read_bytes(),content_type=mime)

    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin')!=self.server.origin:
            return self.send_data({'error':'Yalnızca aynı yerel kaynaktan istek kabul edilir.'},403)
        provided=self.headers.get('X-MOSINT-Token','')
        if not provided.isascii() or not hmac.compare_digest(provided,self.server.token):
            return self.send_data({'error':'Oturum anahtarı geçersiz. Sayfayı yenileyin.'},403)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':
            return self.send_data({'error':'JSON gerekli.'},415)
        try:
            lengths=self.headers.get_all('Content-Length',[])
            if len(lengths)!=1 or not lengths[0].isdigit() or self.headers.get('Transfer-Encoding'):
                return self.send_data({'error':'Geçerli tek Content-Length gerekli.'},400)
            size=int(lengths[0])
            if not 0<size<=MAX_REQUEST:
                return self.send_data({'error':'İstek boyutu sınırı 12 MiB.'},413)
            with self.server.rate_lock:
                now=time.monotonic()
                while self.server.times and self.server.times[0]<now-60:
                    self.server.times.popleft()
                if len(self.server.times)>=60:
                    return self.send_data({'error':'Dakikada 60 istek sınırı. Biraz bekleyin.'},429)
                self.server.times.append(now)
            payload=json.loads(self.rfile.read(size))
            if not isinstance(payload,dict):
                raise ValueError('JSON nesnesi gerekli.')
            if self.path=='/api/settings':
                if not payload or any(name not in ('ipinfo','hibp','oathnet') for name in payload):
                    raise ValueError('Yalnızca ipinfo, hibp veya oathnet ayarı kabul edilir.')
                for name,value in payload.items():
                    if not isinstance(value,str) or len(value)>256 or any(ord(c)<33 or ord(c)>126 for c in value):
                        raise ValueError('Anahtar en fazla 256 görünür ASCII karakteri olabilir.')
                    if name=='hibp' and value and not re.fullmatch(r'[0-9a-fA-F]{32}',value):
                        raise ValueError('HIBP anahtarı 32 onaltılık karakter olmalı.')
                with self.server.key_lock:
                    for name,value in payload.items():
                        if value:self.server.keys[name]=value
                        else:self.server.keys.pop(name,None)
                    configured={name:bool(self.server.keys.get(name)) for name in ('ipinfo','hibp','oathnet')}
                return self.send_data({'saved':any(bool(v) for v in payload.values()),'configured':configured,'storage':'process-memory-only'})
            if self.path not in ('/api/run','/api/batch'):
                return self.send_data({'error':'Bulunamadı.'},404)
            if not self.server.jobs.acquire(blocking=False):
                return self.send_data({'error':'İki işlem zaten çalışıyor. Sonuçları bekleyin.'},429)
            try:
                if self.path=='/api/batch':
                    result=self.run_batch(payload)
                else:
                    result=self.run_tool(payload)
                return self.send_data(result)
            finally:
                self.server.jobs.release()
        except (ValueError,TypeError,KeyError,OverflowError) as exc:
            return self.send_data({'error':str(exc)[:400]},400)
        except Exception:
            return self.send_data({'error':'İşlem tamamlanamadı. Girdiyi, sağlayıcı erişimini ve dosya biçimini kontrol edin. Bilinmeyen sonuç olumlu/olumsuz bulgu sayılmaz.'},502)

    def run_tool(self, payload):
        n=payload.get('id')
        if type(n) is not int or not 1<=n<=FEATURE_COUNT:
            raise ValueError('1–%s arasında özellik numarası gerekli.'%FEATURE_COUNT)
        text=payload.get('text','')
        if not isinstance(text,str) or len(text)>100000:
            raise ValueError('Metin en fazla 100.000 karakter olabilir.')
        # Trim identifiers, preserve byte-sensitive codec and pasted source input.
        if n not in {39,42,51,76,77,78,79,83,84,85,88,107,108,110}:
            text=text.strip()
        with self.server.key_lock:
            keys=dict(self.server.keys)
        feature=catalog(keys)[n-1]
        if not feature['runnable']:
            raise ValueError(feature['note'])
        if n in NETWORK_IDS:
            if payload.get('network_consent') is not True:
                raise ValueError('Bu işlem hedefi dış hizmete/sunucuya gönderir. Ağ iznini açın.')
            result=network_tool(n,text,payload,keys)
        elif n in FILE_IDS:
            result=file_tool(n,payload)
        elif n==99:
            result={'max_concurrent_jobs':2,'tcp_workers':4,'dns_workers_per_job':3,'max_tcp_ports':16,'max_batch_targets':20,
                    'policy':'Sınırlı eşzamanlılık etkin; sınırsız tarama veya kota aşma yok.'}
        elif 100<=n<=105:
            raise ValueError('Bu özellik paneldeki vaka/rapor/ayarlar kontrolleriyle kullanılır.')
        else:
            result=local_tool(n,text,payload)
        return {'feature_id':n,'name':feature['name'],'status':feature['status'],'scope':feature['note'],
                'timestamp':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'result':result}

    def run_batch(self,payload):
        n=payload.get('tool_id')
        targets=payload.get('targets')
        if n not in BATCH_IDS or not isinstance(targets,list) or not 1<=len(targets)<=20 or any(not isinstance(t,str) or len(t)>2000 for t in targets):
            raise ValueError('İzinli yerel araç ve 1–20 hedef (her biri en fazla 2000 karakter) gerekli.')
        rows=[]
        for text in targets:
            try:
                rows.append({'target':text,'result':local_tool(n,text.strip(),{})})
            except (ValueError,TypeError,OverflowError) as exc:
                rows.append({'target':text,'error':str(exc)[:300]})
        return {'feature_id':105,'name':'Toplu yerel işleme','status':'partial','timestamp':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'scope':'En fazla 20 hedef. Dış ağ sorgusu yapılmaz.','result':{'tool_id':n,'rows':rows}}
