"""Small, independently testable tools. All input is data, never executable code."""
import base64
import codecs
import concurrent.futures
import datetime as dt
import email
import hashlib
import html
from html.parser import HTMLParser
import io
import ipaddress
import json
import re
import socket
import ssl
import struct
import time
import unicodedata
from urllib.parse import quote, urlencode, urljoin, urlsplit
import zipfile
import xml.etree.ElementTree as ET

from .network import public_addresses, fetch, fetch_json
from .extra_tools import extra_tool
from .hibp import email_breaches
from .oathnet import breach_summary

B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
MAX_FILE = 8 * 1024 * 1024


def b58encode(data):
    if len(data)>4096:
        raise ValueError('Base58 yerel sınırı: 4096 girdi baytı.')
    n = int.from_bytes(data, 'big')
    s = ''
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return '1' * (len(data) - len(data.lstrip(b'\0'))) + s


def b58decode(s):
    if len(s)>5600:
        raise ValueError('Base58 yerel sınırı: 5600 kodlanmış karakter.')
    n = 0
    for char in s:
        if char not in B58:
            raise ValueError('Base58 karakteri geçersiz.')
        n = n * 58 + B58.index(char)
    return b'\0' * (len(s) - len(s.lstrip('1'))) + (n.to_bytes((n.bit_length()+7)//8, 'big') if n else b'')


def links(items):
    return {'links': [{'label': a, 'url': b} for a, b in items]}


def domain(value):
    host = urlsplit(value if '://' in value else 'https://' + value).hostname or ''
    host = host.rstrip('.').encode('idna').decode('ascii').lower()
    if not re.fullmatch(r'(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host) or any(not x or len(x)>63 or x.startswith('-') or x.endswith('-') for x in host.split('.')):
        raise ValueError('Geçerli bir alan adı gerekli.')
    return host


def file_bytes(data):
    raw = base64.b64decode(data.get('file', ''), validate=True)
    if not raw or len(raw) > MAX_FILE:
        raise ValueError('Dosya boş veya 8 MiB sınırını aşıyor.')
    return raw


class Page(HTMLParser):
    def __init__(self, text, base=''):
        super().__init__(convert_charrefs=True)
        self.links, self.comments, self.icons = [], [], []
        self.base = base
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.links.append(urljoin(self.base, a['href']))
        if tag == 'link' and 'icon' in a.get('rel', '').lower() and a.get('href'):
            self.icons.append(urljoin(self.base, a['href']))

    def handle_comment(self, text):
        self.comments.append(text)


def dns_query(name, typ):
    return fetch_json('https://dns.google/resolve?' + urlencode({'name': name, 'type': typ, 'edns_client_subnet':'0.0.0.0/0'}))


def iocs(text):
    ips = []
    for item in re.findall(r'(?<![\w:])[0-9a-fA-F:.]{3,}(?![\w:])', text):
        try:
            ips.append(str(ipaddress.ip_address(item.strip('.,'))))
        except ValueError:
            pass
    return {'ip': sorted(set(ips)),
            'email': sorted(set(re.findall(r'(?<![\w.+-])[\w.+-]{1,64}@[\w.-]{1,253}\.[a-zA-Z]{2,63}', text))),
            'url': sorted(set(re.findall(r'https?://[^\s<>"\']+', text))),
            'mac': sorted(set(re.findall(r'(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b', text))),
            'wallet_candidates': sorted(set(re.findall(r'\b(?:0x[0-9a-fA-F]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[ac-hj-np-z02-9]{11,87})\b', text)))}


def mmh3(data):
    """MurmurHash3 x86_32, seed zero, signed output."""
    h = 0
    def rol(x, r):
        return ((x << r) | (x >> (32-r))) & 0xffffffff
    def mix(k):
        return (rol(k * 0xcc9e2d51 & 0xffffffff, 15) * 0x1b873593) & 0xffffffff
    for off in range(0, len(data)//4*4, 4):
        h = rol(h ^ mix(int.from_bytes(data[off:off+4], 'little')), 13)
        h = (h * 5 + 0xe6546b64) & 0xffffffff
    tail = data[len(data)//4*4:]
    if tail:
        h ^= mix(int.from_bytes(tail, 'little'))
    h ^= len(data)
    h ^= h >> 16
    h = h * 0x85ebca6b & 0xffffffff
    h ^= h >> 13
    h = h * 0xc2b2ae35 & 0xffffffff
    h ^= h >> 16
    return h if h < 2**31 else h - 2**32


def codec_tool(text, mode):
    enc = not mode.endswith('_decode')
    kind = mode.replace('_encode', '').replace('_decode', '')
    raw = text.encode('utf-8')
    if kind in ('base64','base32','base58'):
        if enc:
            return {'output': {'base64': base64.b64encode, 'base32': base64.b32encode, 'base58': b58encode}[kind](raw).decode() if kind != 'base58' else b58encode(raw)}
        out = {'base64': lambda x: base64.b64decode(x, validate=True), 'base32': base64.b32decode, 'base58': b58decode}[kind](text.strip())
        return {'output': out.decode('utf-8')}
    if kind == 'hex':
        return {'output': raw.hex() if enc else bytes.fromhex(text).decode('utf-8')}
    if kind == 'binary':
        return {'output': ' '.join(format(c, '08b') for c in raw) if enc else bytes(int(x, 2) for x in text.split()).decode('utf-8')}
    if kind == 'url':
        from urllib.parse import unquote
        return {'output': quote(text, safe='') if enc else unquote(text)}
    if kind == 'html':
        return {'output': html.escape(text) if enc else html.unescape(text)}
    raise ValueError('Kodlama modu geçersiz.')


def local_tool(n, text, data):
    if n in (106,107,108,110):
        return extra_tool(n,text,data)
    if n == 11:
        net = ipaddress.ip_network(text, strict=False)
        first, last = int(net.network_address), int(net.broadcast_address)
        usable = net.num_addresses
        if net.version == 4 and net.prefixlen < 31:
            first, last, usable = first+1, last-1, usable-2
        elif net.version == 6 and net.prefixlen < 127:
            first, usable = first+1, usable-1
        address_type=type(net.network_address)
        return {'network': str(net), 'netmask': str(net.netmask), 'total_addresses': net.num_addresses,
                'usable_addresses': usable, 'first_host': str(address_type(first)),
                'last_host': str(address_type(last)), 'broadcast': str(net.broadcast_address) if net.version == 4 else None}
    if n == 12:
        ip = ipaddress.ip_address(text)
        return {'compressed': str(ip), 'expanded': ip.exploded, 'version': ip.version,
                'global': ip.is_global, 'reverse_pointer': ip.reverse_pointer,
                'ipv4_mapped': str(ipaddress.IPv6Address('::ffff:' + str(ip))) if ip.version==4 else str(ip.ipv4_mapped or ''),
                'note': 'IPv4-mapped gösterimi yönlendirme veya gerçek IPv6 bağlantısı sağlamaz.'}
    if n == 13:
        net = str(ipaddress.ip_network(text, strict=False))
        return {'Shodan': 'net:' + net, 'Censys': 'ip: ' + net, 'note': 'Sorgu üretildi; arama yapılmadı.'}
    if n in (23, 34, 41, 57, 58, 69, 89, 90, 91, 94):
        return query_links(n, text)
    if n == 31:
        if not re.fullmatch(r'[\w.-]{1,64}', text):
            raise ValueError('1–64 harf, rakam, nokta, alt çizgi veya tire kullanın.')
        from .profiles import PROFILE_TEMPLATES
        return {**links([(name, template.format(quote(text, safe=''))) for name, template in PROFILE_TEMPLATES]),
                'note': 'Yalnızca 55 profil bağlantısı. Hesap varlığı veya aynı kişiye ait olduğu doğrulanmadı.'}
    if n == 35:
        value = int(text)
        if not 0 <= value < 2**64:
            raise ValueError('64 bit işaretsiz Snowflake gerekli.')
        return {'created_utc': dt.datetime.fromtimestamp(((value >> 22)+1420070400000)/1000, dt.timezone.utc).isoformat(),
                'worker': (value >> 17) & 31, 'process': (value >> 12) & 31, 'increment': value & 4095,
                'note': 'ID biçimi çözülür; hesabın varlığı doğrulanmaz.'}
    if n == 37:
        offset = 76561197960265728
        if text.startswith('[U:1:') and text.endswith(']'):
            account = int(text[5:-1])
        elif text.startswith('STEAM_'):
            a, b = text.split(':')[1:]
            if int(a) not in (0,1):
                raise ValueError('Steam2 auth bit geçersiz.')
            account = int(b)*2+int(a)
        else:
            account = int(text) - offset
        if not 0 <= account <= 0xffffffff:
            raise ValueError('Geçerli Steam2/Steam3/Steam64 bireysel ID gerekli.')
        return {'Steam64': str(account+offset), 'Steam3': '[U:1:%s]'%account, 'Steam2': 'STEAM_0:%s:%s'%(account%2, account//2),
                **links([('Steam profili', 'https://steamcommunity.com/profiles/'+str(account+offset))])}
    if n == 39:
        p = Page(text)
        return {'links': [{'label': u, 'url': u} for u in dict.fromkeys(p.links) if urlsplit(u).hostname in ('linktr.ee', 'beacons.ai', 'bio.link', 'lnk.bio')],
                'note': 'Yapıştırılan HTML incelendi; profil indirilmedi.'}
    if n in (40,49):
        parts = [x.strip() for x in text.split(',')]
        if len(parts) != 3:
            raise ValueError('Virgülle ayrılmış ad, soyad, yıl veya domain gerekli.')
        a, b, c = parts
        tr = str.maketrans('ıİşŞğĞüÜöÖçÇ', 'iIsSgGuUoOcC')
        def simple(s):
            return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', s.translate(tr)).encode('ascii','ignore').decode().lower())
        a,b = simple(a),simple(b)
        if not a or not b:
            raise ValueError('Ad ve soyad gerekli.')
        handles = list(dict.fromkeys([a+b,a+'.'+b,a+'_'+b,a[0]+b,b+a,a+b[0]]))
        if n == 49:
            handles = [v+'@'+domain(c) for v in handles]
        else:
            handles += [a+b+simple(c),a+'.'+b+simple(c)]
        return {'candidates': handles, 'note':'Aday üretimi; hesap varlığı veya sahipliği doğrulanmaz.'}
    if n == 42:
        return {'channel_ids': sorted(set(re.findall(r'UC[a-zA-Z0-9_-]{22}', text))), 'note': 'URL/HTML içindeki ID çıkarılır; kanal tarihi sorgulanmaz.'}
    if n == 46:
        valid = bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}",text)) and len(text)<=254
        if valid:
            local, dom = text.rsplit('@',1)
            valid = len(local)<=64 and not local.startswith('.') and not local.endswith('.') and '..' not in local and '..' not in dom
        return {'syntax_valid':valid, 'note':'Pratik ASCII alt kümesi; teslim edilebilirlik, RFC kapsamının tamamı veya hesap varlığı doğrulanmaz.'}
    if n == 48:
        dom = text.rsplit('@',1)[-1].lower()
        sample = {'yopmail.com','mailinator.com','10minutemail.com','guerrillamail.com','tempmail.com'}
        return {'domain':dom,'in_sample_list': dom in sample,'sample_size': len(sample), 'note':'Küçük örnek liste; listede yok sonucu kalıcı adres kanıtı değildir.'}
    if n == 51:
        msg = email.message_from_string(text)
        received = msg.get_all('Received',[])
        return {'from':msg.get('From'), 'reply_to':msg.get('Reply-To'), 'return_path':msg.get('Return-Path'),
                'received_newest_first': received, 'authentication_results':msg.get_all('Authentication-Results',[]),
                'received_ip_candidates':iocs('\n'.join(received))['ip'], 'note':'Başlık beyanları güvenilir sunucu doğrulaması olmadan taklit edilebilir.'}
    if n in (53,54,55,56):
        if not re.fullmatch(r'\+[1-9]\d{6,14}',text):
            raise ValueError('E.164 biçimi gerekli: +905551234567 (7–15 rakam).')
        if n == 53:
            return {'e164_syntax':True,'note':'Yalnızca biçim; numara tahsisi veya etkinliği doğrulanmaz.'}
        try:
            import phonenumbers as pn
            from phonenumbers import carrier, geocoder, timezone
        except ImportError:
            raise ValueError('Ek paket gerekli: requirements-optional.txt içindeki phonenumbers kurulmalı.') from None
        phone = pn.parse(text, None)
        return {'valid_plan':pn.is_valid_number(phone),'possible':pn.is_possible_number(phone),
                'region':pn.region_code_for_number(phone), 'description':geocoder.description_for_number(phone,'tr'),
                'carrier_original_allocation':carrier.name_for_number(phone,'tr'),'type':pn.number_type(phone),
                'timezones':timezone.time_zones_for_number(phone), 'note':'Numara planı tahmini. Taşınan numaralarda güncel operatör, gerçek konum veya yerel saat doğrulanmaz.'}
    if n in (76,77,78):
        return codec_tool(text, data.get('mode','base64_encode' if n==76 else 'hex_encode' if n==77 else 'url_encode'))
    if n == 79:
        def caesar(k):
            return ''.join(chr((ord(c)-(65 if c.isupper() else 97)+k)%26+(65 if c.isupper() else 97)) if c.isascii() and c.isalpha() else c for c in text)
        return {'ROT13':codecs.decode(text,'rot_13'),'shifts':{str(k):caesar(k) for k in range(1,26)}}
    if n == 80:
        parts = text.split('.')
        if len(parts)!=3:
            raise ValueError('Üç bölümlü JWT gerekli.')
        def decode(p):
            return json.loads(base64.urlsafe_b64decode(p + '='*(-len(p)%4)))
        return {'header':decode(parts[0]),'payload':decode(parts[1]),'signature_verified':False,'note':'İmza doğrulanmadı. İçerik güvenilir kabul edilemez.'}
    if n == 81:
        candidates=[]
        if re.fullmatch('[0-9a-fA-F]+',text):
            candidates={32:['MD5','NTLM'],40:['SHA-1'],64:['SHA-256'],96:['SHA-384'],128:['SHA-512']}.get(len(text),[])
        if re.fullmatch(r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}',text):
            candidates.append('bcrypt')
        return {'candidates':candidates,'note':'Biçim ve uzunluk tahmini; kesin algoritma tespiti değildir.'}
    if n == 82:
        try:
            num=float(text)
            unit=data.get('mode','seconds')
            value=dt.datetime.fromtimestamp(num/(1000 if unit=='milliseconds' else 1),dt.timezone.utc)
        except ValueError:
            value=dt.datetime.fromisoformat(text.replace('Z','+00:00'))
            if value.tzinfo is None:
                raise ValueError('ISO tarih UTC ofseti içermeli.')
        return {'utc':value.astimezone(dt.timezone.utc).isoformat(),'unix_seconds':value.timestamp(),'unix_milliseconds':int(value.timestamp()*1000)}
    if n == 83:
        return iocs(text)
    if n == 84:
        if data.get('mode')=='refang':
            output=text.replace('hxxps','https').replace('hxxp','http').replace('[.]','.').replace('[://]','://').replace('[@]','@')
        else:
            output=text.replace('https://','hxxps[://]').replace('http://','hxxp[://]').replace('.','[.]').replace('@','[@]')
        return {'output':output}
    if n == 85:
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        codes='.- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- .--. --.- .-. ... - ..- ...- .-- -..- -.-- --.. ----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----.'.split()
        morse=dict(zip(alphabet,codes))
        mode=data.get('mode','morse_encode')
        if mode=='decimal_encode':
            return {'output':' '.join(str(c) for c in text.encode('utf-8')), 'note':'ASCII dışı metin UTF-8 baytlarıyla temsil edilir.'}
        if mode=='decimal_decode':
            return {'output':bytes(int(c) for c in text.split()).decode('utf-8')}
        if mode=='morse_decode':
            rev={v:k for k,v in morse.items()}
            return {'output':''.join(' ' if c=='/' else rev.get(c,'?') for c in text.split())}
        return {'output':' '.join('/' if c==' ' else morse.get(c,'?') for c in text.upper())}
    if n == 86:
        host=text.strip()
        return {'ascii':host.encode('idna').decode('ascii'),'unicode':host.encode('ascii').decode('idna') if host.isascii() else host,
                'note':'IDNA dönüşümü güvenilirlik veya homograf güvenliği garantisi değildir.'}
    if n == 87:
        if re.fullmatch(r'0x[0-9a-fA-F]{40}',text):
            return {'format':'Ethereum','syntax_match':True,'checksum_verified':False,'note':'EIP-55 checksum ve zincir varlığı doğrulanmadı.'}
        if text.startswith(('1','3')):
            raw=b58decode(text)
            valid=len(raw)==25 and hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4]==raw[-4:]
            return {'format':'Bitcoin Base58Check','checksum_verified':valid,'note':'Zincir, bakiye veya sahiplik sorgulanmadı.'}
        return {'syntax_match':False,'note':'Yalnızca ETH biçimi ve BTC Base58Check desteklenir; Bech32/XMR entegrasyonu gerekli.'}
    if n == 88:
        current=text
        steps=[]
        for _ in range(5):
            output=None
            if re.fullmatch(r'(?:[0-9a-fA-F]{2})+', current):
                try:
                    output=bytes.fromhex(current).decode('utf-8'); kind='hex'
                except (ValueError,UnicodeError):
                    pass
            if output is None and re.fullmatch(r'[A-Za-z0-9+/]+={0,2}',current) and len(current)%4==0:
                try:
                    output=base64.b64decode(current,validate=True).decode('utf-8'); kind='base64'
                except (ValueError,UnicodeError):
                    pass
            if output is None or output==current or not output.isprintable():
                break
            steps.append({'encoding':kind,'output':output}); current=output
        return {'output':current,'steps':steps,'note':'En fazla 5 katman; sezgisel Base64/Hex çözümü, doğruluk garantisi yok.'}
    if n == 95:
        rows=[{'iso':'TR','name':'Türkiye','phone':'+90','vehicle':'TR'},{'iso':'DE','name':'Almanya','phone':'+49','vehicle':'D'},
              {'iso':'GB','name':'Birleşik Krallık','phone':'+44','vehicle':'UK'},{'iso':'US','name':'ABD','phone':'+1','vehicle':'USA'},
              {'iso':'FR','name':'Fransa','phone':'+33','vehicle':'F'},{'iso':'NL','name':'Hollanda','phone':'+31','vehicle':'NL'}]
        return {'matches':[r for r in rows if not text or any(text.casefold() in v.casefold() for v in r.values())],
                'note':'6 ülkelik hızlı başvuru; plaka sahibi veya tüm ülkeler sorgulanmaz.'}
    raise ValueError('Bu araç için yerel işleyici yok.')


def query_links(n, text):
    q=quote(text,safe='')
    if n==23:
        return {**links([('Wayback takvimi','https://web.archive.org/web/*/'+domain(text))]),'note':'Arşiv arama bağlantısı; snapshot indirilmedi.'}
    if n==34:
        digest=hashlib.md5(text.strip().lower().encode()).hexdigest()
        return {**links([('Gravatar','https://www.gravatar.com/avatar/'+digest+'?d=404')]),'md5':digest,'note':'E-posta hashli bağlantı üretildi; profil varlığı doğrulanmadı.'}
    if n==41:
        return links([('Wikipedia katkılar','https://tr.wikipedia.org/wiki/Special:Contributions/'+q),('Ekşi arama','https://eksisozluk.com/?q='+q)])
    if n==57:
        if not re.fullmatch(r'\+[1-9]\d{6,14}',text):
            raise ValueError('E.164 numarası gerekli.')
        return {**links([('WhatsApp','https://wa.me/'+text[1:]),('Telegram','https://t.me/+'+text[1:])]),'note':'Bağlantı üretildi; hesap varlığı kontrol edilmedi.'}
    if n==58:
        digits=re.sub(r'\D','',text)
        if not 7<=len(digits)<=15:
            raise ValueError('7–15 haneli numara gerekli.')
        return links([('Telefon arama','https://www.google.com/search?q='+quote('"+'+digits+'" OR "'+digits+'"'))])
    if n==69:
        u=urlsplit(text)
        if u.scheme not in ('https','http') or not u.hostname or u.username or u.password:
            raise ValueError('Genel bir görsel HTTP/HTTPS URL adresi gerekli.')
        return links([('Google Lens','https://lens.google.com/uploadbyurl?url='+q),('Yandex Images','https://yandex.com/images/search?rpt=imageview&url='+q),('TinEye','https://tineye.com/search?url='+q),('Bing','https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl='+q)])
    if n==89:
        host=domain(text)
        queries=['site:'+host,'site:'+host+' filetype:pdf','site:'+host+' intitle:"index of"','site:'+host+' inurl:admin']
        return {'queries':queries,**links([(x,'https://www.google.com/search?q='+quote(x)) for x in queries])}
    if n==90:
        # Defensive inventory only: never retrieve, validate or use discovered secrets.
        org=text.strip()
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',org):
            raise ValueError('Kendi kuruluşunuzun kısa adını kullanın.')
        query='org:'+org+' path:.env'
        return {'scope':'Kendi kuruluşunuz için savunma envanteri; sır içerikleri alınmaz.',
                **links([('GitHub dosya envanteri','https://github.com/search?type=code&q='+quote(query)),('GitLab proje arama','https://gitlab.com/search?search='+q)])}
    if n==91:
        return links([('Pastebin arama','https://www.google.com/search?q='+quote('site:pastebin.com "'+text+'"'))])
    if n==94:
        return links([('Uçak arama','https://www.flightradar24.com/data/aircraft/'+q),('Gemi arama','https://www.marinetraffic.com/en/ais/index/search/all/keyword:'+q)])
    raise ValueError('Sorgu desteklenmiyor.')


def network_tool(n, text, data, keys):
    if n==111:
        return breach_summary(text,keys.get('oathnet',''))
    if n==50:
        return email_breaches(text,keys.get('hibp',''))
    if n in (1,2):
        ip=ipaddress.ip_address(text)
        if not ip.is_global:
            raise ValueError('Genel IP adresi gerekli.')
        token=keys.get('ipinfo','')
        if token:
            return {'source':'IPinfo Lite (isteğe bağlı alternatif)','data':fetch_json('https://api.ipinfo.io/lite/'+str(ip),{'Authorization':'Bearer '+token}),
                    'note':'Ülke düzeyi tahmin; şehir, posta kodu, koordinat ve kişi konumu sağlanmaz. Anahtarı silerek anahtarsız sağlayıcıya dönebilirsiniz.'}
        fields='ip,success,message,type,country,country_code,region,city,postal,latitude,longitude,connection,timezone'
        result=fetch_json('https://ipwho.is/'+str(ip)+'?'+urlencode({'fields':fields}))
        if not isinstance(result,dict) or result.get('success') is not True:
            message=str(result.get('message','Geçersiz sağlayıcı yanıtı.'))[:200] if isinstance(result,dict) else 'Geçersiz sağlayıcı yanıtı.'
            raise ValueError('IP sorgusu tamamlanamadı: '+message)
        try:
            matches=ipaddress.ip_address(result.get('ip',''))==ip
        except (ValueError,TypeError):
            matches=False
        if not matches:
            raise ValueError('IP sağlayıcısı sorgulanan adresle eşleşen bir yanıt döndürmedi.')
        if n==2 and (not isinstance(result.get('connection'),dict) or not any(result['connection'].get(k) for k in ('asn','isp','org'))):
            raise ValueError('IP sağlayıcısı bu adres için ASN/ISP bilgisi döndürmedi.')
        return {'source':'ipwho.is (anahtarsız)','data':result,
                'note':'API anahtarı gerekmez. Konum verisi yaklaşık ağ konumudur; kişi veya ev konumu kanıtı değildir. Sağlayıcı kotası ve erişim koşulları geçerlidir.'}
    if n in (5,6,10):
        ports=[int(p.strip()) for p in data.get('ports','80,443').split(',')]
        if not 1<=len(ports)<=16 or any(not 1<=p<=65535 for p in ports):
            raise ValueError('Tek hedef için en fazla 16 TCP portu (1–65535).')
        if data.get('authorized') is not True:
            raise ValueError('Aktif test için hedef üzerinde yetkinizi onaylayın.')
        host,ips=public_addresses(text,ports[0])
        def check(port):
            start=time.monotonic()
            try:
                with socket.create_connection((ips[0],port),timeout=1.5) as sock:
                    result={'port':port,'state':'open','latency_ms':round((time.monotonic()-start)*1000,2)}
                    if n==6:
                        sock.settimeout(0.5)
                        try:
                            result['passive_banner']=sock.recv(512).decode('utf-8','replace')
                        except socket.timeout:
                            result['passive_banner']='Yanıt yok; veri gönderilmedi.'
                    return result
            except OSError:
                return {'port':port,'state':'closed_or_filtered'}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            rows=list(pool.map(check,ports))
        return {'host':host,'address':ips[0],'tcp':rows,'note':'TCP bağlantı testi; UDP/ICMP ve servis sürümü doğrulaması yok.'}
    if n==15:
        return {'source':'api.ipify.org','data':fetch_json('https://api.ipify.org?format=json')}
    if n==16:
        return {'source':'RDAP (WHOIS yerine yapılandırılmış kayıt verisi)', 'data':fetch_json('https://rdap.org/domain/'+domain(text))}
    if n in (17,47):
        host=domain(text.rsplit('@',1)[-1])
        types=['MX'] if n==47 else ['A','AAAA','MX','TXT','NS','CNAME','SOA']
        def query(typ):
            d=dns_query(host,typ)
            return typ,{'dns_status':d.get('Status'),'answers':d.get('Answer',[]),'authenticated_data':d.get('AD',False)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            rows=dict(pool.map(query,types))
        return {'source':'Google Public DNS DoH','domain':host,'records':rows,
                'note':'MX kaydı posta kabulü veya hesap varlığı garantisi değildir; Null MX posta kabul etmediğini bildirir.'}
    if n==18:
        host=domain(text)
        rows=fetch_json('https://crt.sh/?'+urlencode({'q':'%.'+host,'output':'json'}))
        names=sorted({name for row in rows for name in row.get('name_value','').splitlines() if name.endswith('.'+host)})
        return {'source':'crt.sh','names':names[:2000],'note':'Pasif sertifika kayıtları; canlılık doğrulanmaz, brute force yapılmaz.'}
    if n==19:
        host,ips=public_addresses(domain(text))
        with socket.create_connection((ips[0],443),timeout=4) as raw:
            with ssl.create_default_context().wrap_socket(raw,server_hostname=host) as sock:
                return {'host':host,'tls_version':sock.version(),'cipher':sock.cipher(),'certificate':sock.getpeercert(),'verified':True}
    if n==22:
        host=domain(text)
        result={}
        for path in ('robots.txt','sitemap.xml'):
            r=fetch('https://'+host+'/'+path)
            result[path]={'status':r['status'],'content':r['body'].decode('utf-8','replace')[:40000]}
        return result
    if n in (20,21,24,25,26,27,29,92,73):
        r=fetch(text)
        source=r['body'].decode('utf-8','replace')
        if n in (29,92):
            return {'chain':r['chain'],'final_url':r['url'],'note':'Hedef sunuculara GET isteği gönderildi; yanıt betikleri çalıştırılmadı.'}
        if n==20:
            headers=['strict-transport-security','content-security-policy','x-frame-options','x-content-type-options','referrer-policy','permissions-policy']
            return {'url':r['url'],'http_status':r['status'],'headers':r['headers'],'missing':[h for h in headers if h not in r['headers']], 'note':'Başlık varlığı güvenlik garantisi veya zafiyet kanıtı değildir.'}
        if n in (21,24):
            hay=source.lower()+' '+json.dumps(r['headers']).lower()
            markers=['wordpress','wp-content','drupal','next.js','__next','react','nginx','apache','cloudflare','cf-ray','akamai','cloudfront']
            return {'url':r['url'],'http_status':r['status'],'hints':[m for m in markers if m in hay],'note':'İmza tabanlı ipuçları; teknoloji/WAF yokluğu veya varlığı kesinleştirilemez.'}
        page=Page(source,r['url'])
        if n==25:
            host=urlsplit(r['url']).hostname
            return {'url':r['url'],'http_status':r['status'],'internal':list(dict.fromkeys(u for u in page.links if urlsplit(u).hostname==host))[:2000],
                    'external':list(dict.fromkeys(u for u in page.links if urlsplit(u).hostname!=host))[:2000]}
        if n==26:
            return {'url':r['url'],'http_status':r['status'],'emails':iocs(source)['email'],'phone_candidates': sorted(set(re.findall(r'\+?\d[\d ()-]{7,}\d',source)))[:200],
                    'note':'Regex adayları; telefon/e-posta doğrulanmaz.'}
        if n==27:
            return {'url':r['url'],'http_status':r['status'],'comments':page.comments[:500]}
        if n==73:
            icon=page.icons[0] if page.icons else urljoin(r['url'],'/favicon.ico')
            image=fetch(icon)
            return {'url':image['url'],'status':image['status'],'bytes':len(image['body']),'content_type':image['headers'].get('content-type'),
                    'sha256':hashlib.sha256(image['body']).hexdigest(),'signature':signature(image['body']),
                    'note':'İkon indirildi ve bellekte analiz edildi; diske yazılmadı.'}
    if n==32:
        if not re.fullmatch(r'[A-Za-z0-9-]{1,39}',text):
            raise ValueError('Geçerli GitHub kullanıcı adı gerekli.')
        user=fetch_json('https://api.github.com/users/'+text)
        repos=fetch_json('https://api.github.com/users/'+text+'/repos?per_page=30&sort=updated')
        return {'source':'GitHub public REST','profile':user,'repositories_first_30':repos,'note':'İlk 30 repo; silinen/özel repolar veya hesap sahipliği çıkarımı yok.'}
    if n==36:
        code=text.rsplit('/',1)[-1]
        if not re.fullmatch(r'[A-Za-z0-9_-]{2,64}',code):
            raise ValueError('Geçerli davet kodu gerekli.')
        return {'source':'Discord public invite','data':fetch_json('https://discord.com/api/v10/invites/'+code+'?with_counts=true'),
                'note':'Kamuya açık davet verisi; kapalı kanallara erişim yok, boost alanı sağlayıcıya bağlı.'}
    if n==43:
        name=text.rstrip('/').rsplit('/',1)[-1].lstrip('@')
        if not re.fullmatch('[A-Za-z0-9_]{5,32}',name):
            raise ValueError('Genel kanal kullanıcı adı gerekli.')
        r=fetch('https://t.me/'+name)
        text_body=r['body'].decode('utf-8','replace')
        matches=re.findall(r'<meta\s+(?:property|name)=["\'](og:[^"\']+)["\']\s+content=["\']([^"\']*)',text_body)
        return {'source':'t.me public preview','metadata':dict((k,html.unescape(v)) for k,v in matches),'note':'Yalnızca genel HTML önizlemesi; üye sayısı her zaman bulunmaz.'}
    raise ValueError('Bu entegrasyonun ağ işleyicisi henüz uygulanmadı.')


def signature(raw):
    signatures=[(b'\x89PNG\r\n\x1a\n','PNG'),(b'\xff\xd8\xff','JPEG'),(b'%PDF-','PDF'),(b'PK\x03\x04','ZIP/OOXML'),
                (b'MZ','DOS/PE candidate'),(b'\x7fELF','ELF'),(b'GIF8','GIF'),(b'Rar!','RAR'),(b'RIFF','RIFF container')]
    return next((label for magic,label in signatures if raw.startswith(magic)),'Unknown')


def safe_zip(raw):
    archive=zipfile.ZipFile(io.BytesIO(raw))
    entries=archive.infolist()
    if len(entries)>2000 or sum(e.file_size for e in entries)>64*1024*1024:
        archive.close()
        raise ValueError('Arşiv güvenlik sınırı: 2000 girdi / 64 MiB açılmış boyut.')
    if any(e.file_size>8*1024*1024 or e.file_size/max(e.compress_size,1)>200 for e in entries):
        archive.close()
        raise ValueError('Arşiv sıkıştırma oranı veya girdi boyutu sınırı aşıldı.')
    return archive


def file_tool(n, data):
    raw=file_bytes(data)
    if n==109:
        expected=data.get('text','').strip().lower()
        if not re.fullmatch('[0-9a-f]{64}',expected):
            raise ValueError('Beklenen SHA-256 özeti tam 64 onaltılık karakter olmalı.')
        actual=hashlib.sha256(raw).hexdigest()
        return {'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected,'bytes':len(raw),
                'note':'Dosya özeti karşılaştırıldı; zararsızlık veya yayıncı kimliği doğrulanmaz. Beklenen özeti güvenilir kaynaktan alın.'}
    if n==28:
        return {'murmurhash3_base64_signed':mmh3(base64.encodebytes(raw)),'bytes':len(raw),
                'note':'Shodan tarzı satır sonlu Base64 üzerine MurmurHash3; ağ sorgusu yapılmadı.'}
    if n==65:
        return {algo:hashlib.new(algo,raw).hexdigest() for algo in ('md5','sha1','sha256','sha512')}
    if n==66:
        return {'signature_hint':signature(raw),'first_32_bytes':raw[:32].hex(),'note':'Sınırlı imza tablosu; dosyanın güvenli olduğu veya gerçek tipinin kesinleştiği anlamına gelmez.'}
    if n==67:
        values=re.findall(rb'[\x20-\x7e]{4,}',raw)
        utf=re.findall(r'[^\x00-\x1f\x7f]{4,}',raw.decode('utf-8','replace'))
        return {'ascii':[x.decode()[:2000] for x in values[:1000]],'utf8_candidates':[s[:2000] for s in utf[:1000]],'truncated':len(values)>1000}
    if n==64:
        with safe_zip(raw) as archive:
            if 'docProps/core.xml' not in archive.namelist():
                raise ValueError('OOXML docProps/core.xml bulunamadı; eski DOC/XLS desteklenmez.')
            xml=archive.read('docProps/core.xml')
            if len(xml)>65536 or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
                raise ValueError('XML güvenlik sınırı.')
            root=ET.fromstring(xml)
            return {'core_properties':{e.tag.split('}')[-1]:e.text for e in root},'note':'Metadata beyanlarıdır; bilgisayar kullanıcı adı her dosyada bulunmaz.'}
    if n==74:
        if not zipfile.is_zipfile(io.BytesIO(raw)):
            raise ValueError('Yalnızca ZIP desteklenir; RAR için entegrasyon gerekli.')
        with safe_zip(raw) as archive:
            return {'entries':[{'name':e.filename,'bytes':e.file_size,'compressed_bytes':e.compress_size,'modified':list(e.date_time),'encrypted':bool(e.flag_bits&1)} for e in archive.infolist()],
                    'note':'İçerik diske çıkarılmadı; dosya adları güvenilmeyen veridir.'}
    if n==72:
        boundary=None
        if raw.startswith(b'\xff\xd8'):
            idx=raw.rfind(b'\xff\xd9')
            if idx>=0: boundary=idx+2
        elif raw.startswith(b'\x89PNG'):
            pos=8
            while pos+12<=len(raw):
                length=int.from_bytes(raw[pos:pos+4],'big')
                if raw[pos+4:pos+8]==b'IEND':
                    boundary=pos+12; break
                pos+=12+length
        return {'image_end_offset':boundary,'trailing_bytes':len(raw)-boundary if boundary is not None else None,
                'note':'JPEG/PNG sonuna eklenen veri kontrolü; LSB/steganografi veya temiz dosya kanıtı değildir.'}
    if n==63:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError('Ek paket gerekli: pypdf (requirements-optional.txt).') from None
        reader=PdfReader(io.BytesIO(raw),strict=True)
        if reader.is_encrypted:
            raise ValueError('Şifreli PDF desteklenmiyor.')
        return {'metadata':dict(reader.metadata or {}),'note':'Yalnızca PDF metadata beyanları; güvenilir kimlik doğrulaması değildir.'}
    if n==71:
        try:
            import mutagen
        except ImportError:
            raise ValueError('Ek paket gerekli: mutagen (requirements-optional.txt).') from None
        media=mutagen.File(io.BytesIO(raw))
        if not media:
            raise ValueError('Bu medya formatı mutagen tarafından tanınmadı.')
        return {'info':media.info.pprint(),'tags':{str(k):str(v) for k,v in (media.tags or {}).items()},'note':'Desteklenen ses/MP4 formatları; tüm video codec ve cihazları kapsamaz.'}
    if n in (61,62,75):
        try:
            from PIL import Image, ExifTags
        except ImportError:
            raise ValueError('Ek paket gerekli: Pillow (requirements-optional.txt).') from None
        Image.MAX_IMAGE_PIXELS=16_000_000
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.width*image.height>16_000_000:
                    raise ValueError('Görsel en fazla 16 megapiksel olabilir.')
                if n==75:
                    # Pixel-only fresh PNG: no EXIF, ICC, comments, PNG text or source info.
                    pixels=Image.frombytes('RGBA',image.size,image.convert('RGBA').tobytes())
                    output=io.BytesIO(); pixels.save(output,format='PNG')
                    cleaned=output.getvalue()
                    if len(cleaned)>MAX_FILE:
                        raise ValueError('Temizlenmiş çıktı 8 MiB sınırını aşıyor.')
                    return {'download':{'name':'metadata-clean.png','mime':'image/png','base64':base64.b64encode(cleaned).decode()},'note':'Yeni PNG yalnızca piksellerden oluşturuldu; animasyon ve kaynak format korunmaz.'}
                exif=image.getexif()
                metadata={ExifTags.TAGS.get(k,str(k)):str(v) for k,v in exif.items()}
                result={'format':image.format,'width':image.width,'height':image.height,'exif':metadata}
                if n==62:
                    gps=exif.get_ifd(34853) if 34853 in exif else {}
                    if gps and all(k in gps for k in (1,2,3,4)):
                        def coord(values,ref):
                            a,b,c=[float(v) for v in values]
                            return (a+b/60+c/3600)*(-1 if ref in ('S','W') else 1)
                        lat,lon=coord(gps[2],gps[1]),coord(gps[4],gps[3])
                        if abs(lat)<=90 and abs(lon)<=180:
                            result.update({'latitude':lat,'longitude':lon,**links([('OpenStreetMap',f'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}')])})
                    result['note']='GPS varsa metadata beyanı olarak gösterilir; çekim yeri doğrulanmaz.'
                return result
    raise ValueError('Dosya işleyicisi yok.')
