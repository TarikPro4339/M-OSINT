"""Five bounded local utilities added with the release version unchanged."""
import difflib
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def sections(text):
    if '\n---\n' not in text.replace('\r\n','\n'):
        raise ValueError('İki bölümü ayrı bir satırdaki --- ile ayırın.')
    return text.replace('\r\n','\n').split('\n---\n',1)


def extra_tool(n,text,data):
    if n==106:
        if any(ord(c)<33 or ord(c)==127 for c in text) or '\\' in text:
            raise ValueError('URL boşluk, denetim karakteri veya ters eğik çizgi içeremez.')
        u=urlsplit(text)
        if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:
            raise ValueError('Kullanıcı bilgisi içermeyen tam HTTP/HTTPS URL gerekli.')
        port=u.port
        if port is not None and not 1<=port<=65535:
            raise ValueError('URL portu 1–65535 aralığında olmalı.')
        pairs=parse_qsl(u.query,keep_blank_values=True,max_num_fields=500)
        known={'gclid','dclid','fbclid','msclkid','mc_cid','mc_eid','_ga'}
        removed=[k for k,v in pairs if k.casefold().startswith('utm_') or k.casefold() in known]
        kept=[(k,v) for k,v in pairs if not (k.casefold().startswith('utm_') or k.casefold() in known)]
        clean=urlunsplit((u.scheme,u.netloc,u.path,urlencode(kept) if removed else u.query,u.fragment))
        return {'scheme':u.scheme,'host':u.hostname,'port':port,'path':u.path or '/',
                'query_parameters':[{'name':k,'value':v} for k,v in pairs], 'removed_parameters':removed,
                'clean_url':clean,'fragment':u.fragment,
                'note':'Yerel ayrıştırma; URL ziyaret edilmedi. Temizleme imzalı URL geçerliliğini bozabilir.'}
    if n==107:
        first,second=sections(text)
        def values(part):
            lines=part.splitlines()
            if len(lines)>2000:
                raise ValueError('Her IOC listesi en fazla 2000 satır olabilir.')
            return {line.strip() for line in lines if line.strip()}
        a,b=values(first),values(second)
        return {'common':sorted(a&b),'only_first':sorted(a-b),'only_second':sorted(b-a),
                'first_unique_count':len(a),'second_unique_count':len(b),
                'note':'Satır başı/sonu boşlukları ve boş satırlar ayıklanır. Büyük/küçük harfe duyarlı tam metin karşılaştırması; ağ sorgusu yok.'}
    if n==108:
        pattern=r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}"
        def mask(match):
            local,host=match.group().rsplit('@',1)
            return local[0]+'***@'+host
        output,count=re.subn(pattern,mask,text)
        return {'masked_text':output,'masked_count':count,
                'note':'Pratik ASCII e-posta adayları maskelenir; tüm kişisel verileri veya uluslararası adresleri kapsayan anonimleştirme değildir.'}
    if n==110:
        first,second=sections(text)
        a,b=first.splitlines(),second.splitlines()
        if max(len(a),len(b))>1000:
            raise ValueError('Her metin en fazla 1000 satır olabilir.')
        lines=list(difflib.unified_diff(a,b,fromfile='ilk_metin',tofile='ikinci_metin',lineterm=''))
        return {'identical_lines':a==b,'unified_diff':'\n'.join(lines),'first_line_count':len(a),'second_line_count':len(b),
                'note':'Satır bazlı yerel karşılaştırma. Son satır sonlandırıcısının varlığı ve CRLF/LF farkı karşılaştırılmaz.'}
    raise ValueError('Yerel ek araç numarası geçersiz.')
