"""Bounded, public-only HTTP transport. No proxy environment or automatic redirects.

Resolve once, validate every answer, then connect to that exact address. TLS
still verifies the original hostname. A redirect always repeats these checks.
"""
import concurrent.futures
import http.client
import ipaddress
import json
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit, urljoin
from . import VERSION

MAX_BODY = 1024 * 1024
UA = "M-OSINT/"+VERSION+" (authorized public-source research)"
_resolver = concurrent.futures.ThreadPoolExecutor(max_workers=4)
_dns_slots = threading.BoundedSemaphore(4)


def public_addresses(host, port=443):
    if not host or '%' in host or host.lower().endswith(('.local', '.localhost', '.onion')):
        raise ValueError("Yerel, onion veya kapsamlı IPv6 hedefi engellendi.")
    host = host.rstrip('.').encode('idna').decode('ascii')
    if not _dns_slots.acquire(blocking=False):
        raise ValueError("DNS kapasitesi dolu; biraz sonra tekrar deneyin.")
    def resolve():
        try:
            return socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        finally:
            _dns_slots.release()
    future = _resolver.submit(resolve)
    try:
        answers = future.result(timeout=4)
    except concurrent.futures.TimeoutError:
        raise ValueError("DNS zaman aşımı.") from None
    except socket.gaierror:
        raise ValueError("Hedef adı çözümlenemedi. İnternet bağlantısını, DNS erişimini ve hedefi kontrol edin.") from None
    addresses = list(dict.fromkeys(a[4][0] for a in answers))
    if not addresses:
        raise ValueError("DNS yanıtı yok.")
    for value in addresses:
        ip = ipaddress.ip_address(value)
        # Block transition mechanisms too: global IPv6 may tunnel to a private IPv4.
        if not ip.is_global or (ip.version == 6 and
                (ip.ipv4_mapped or ip.sixtofour or ip.teredo)):
            raise ValueError("Yalnızca genel IP hedeflerine izin verilir.")
    return host, addresses


def parse_url(value):
    if any(ord(c) < 33 or ord(c) == 127 for c in value) or '\\' in value:
        raise ValueError("URL boşluk veya denetim karakteri içeremez.")
    value = value if '://' in value else 'https://' + value
    u = urlsplit(value)
    if u.scheme not in ('http', 'https') or u.username is not None or u.password is not None or not u.hostname:
        raise ValueError("Kimlik bilgisi içermeyen HTTP/HTTPS adresi gerekli.")
    port = u.port if u.port is not None else (443 if u.scheme == 'https' else 80)
    if port not in (80, 443):
        raise ValueError("Web sorguları yalnızca 80/443 portlarını kullanır.")
    return u, port


class PinnedHTTP(http.client.HTTPConnection):
    def __init__(self, host, port, address, secure):
        super().__init__(host, port, timeout=4)
        self.address = address
        self.secure = secure

    def connect(self):
        addresses=[self.address]+list(getattr(self,'fallback_addresses',[]))[:3]
        deadline=getattr(self,'deadline',time.monotonic()+20)
        for index,address in enumerate(addresses):
            remaining=deadline-time.monotonic()
            if remaining<=0:
                raise TimeoutError('HTTP toplam süre sınırı aşıldı.')
            try:
                raw = socket.create_connection((address, self.port), timeout=min(4,remaining))
            except OSError:
                if index+1==len(addresses):raise
                continue
            if self.secure:
                try:
                    raw.settimeout(min(4,max(0.1,deadline-time.monotonic())))
                    raw = ssl.create_default_context().wrap_socket(raw, server_hostname=self.host)
                except BaseException:
                    raw.close()
                    raise
            self.sock = raw
            return


def fetch(value, *, headers=None, max_body=MAX_BODY, redirects=4):
    chain = []
    seen = set()
    started = time.monotonic()
    for hop in range(redirects + 1):
        if time.monotonic() - started > 20:
            raise ValueError("HTTP toplam süre sınırı aşıldı.")
        u, port = parse_url(value)
        host, addresses = public_addresses(u.hostname, port)
        clean_url = u.geturl().split('#')[0]
        if clean_url in seen:
            raise ValueError("Yönlendirme döngüsü.")
        seen.add(clean_url)
        conn = PinnedHTTP(host, port, addresses[0], u.scheme == 'https')
        conn.fallback_addresses=addresses[1:4]
        conn.deadline=started+20
        def abort_connection(connection=conn):
            sock=getattr(connection,'sock',None)
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            connection.close()
        deadline=threading.Timer(max(0.1,20-(time.monotonic()-started)),abort_connection)
        deadline.daemon=True
        deadline.start()
        try:
            # Adapter credentials may never follow redirects to another host.
            outgoing = dict(headers or {}) if hop == 0 else {}
            outgoing.update({'User-Agent': UA, 'Accept-Encoding': 'identity', 'Connection': 'close'})
            path = (u.path or '/') + ('?' + u.query if u.query else '')
            conn.request('GET', path, headers=outgoing)
            response = conn.getresponse()
            rh = {k.lower(): v for k, v in response.getheaders()}
            chain.append({'url': clean_url, 'status': response.status})
            if response.status in (301, 302, 303, 307, 308) and rh.get('location'):
                target = urljoin(clean_url, rh['location'])
                if u.scheme == 'https' and urlsplit(target).scheme != 'https':
                    raise ValueError("HTTPS → HTTP yönlendirmesi engellendi.")
                if hop == redirects:
                    raise ValueError("Yönlendirme sınırı aşıldı.")
                value = target
                continue
            chunks, total = [], 0
            while True:
                if time.monotonic() - started > 20:
                    raise ValueError("HTTP toplam süre sınırı aşıldı.")
                # read1 returns after one buffered/raw read; a peer cannot keep a
                # read(n) alive forever by dripping a byte before each timeout.
                part = response.read1(min(65536, max_body + 1 - total))
                if not part:
                    break
                chunks.append(part)
                total += len(part)
                if total > max_body:
                    raise ValueError("Yanıt boyutu sınırı aşıldı.")
            if rh.get('content-encoding', 'identity') != 'identity':
                raise ValueError("Sıkıştırılmış HTTP yanıtı desteklenmiyor.")
            length=rh.get('content-length')
            if length is not None and 'transfer-encoding' not in rh and response.status not in (204,304):
                if not length.isascii() or not length.isdigit() or len(length)>12 or int(length)!=total:
                    raise ValueError('HTTP yanıtı eksik veya Content-Length bilgisi tutarsız; sonuç bilinmiyor.')
            return {'url': clean_url, 'status': response.status, 'headers': rh,
                    'body': b''.join(chunks), 'chain': chain}
        finally:
            deadline.cancel()
            conn.close()
    raise ValueError("Yönlendirme sınırı.")


def fetch_json(url, headers=None):
    r = fetch(url, headers=headers)
    if r['status'] != 200:
        raise ValueError("Sağlayıcı HTTP %s döndürdü; kota, anahtar veya erişimi kontrol edin." % r['status'])
    return json.loads(r['body'])
