"""Single-email OathNet breach metadata. Never expose raw credential rows."""
import json
import re
from collections import Counter
from urllib.parse import urlencode
from .network import fetch


def breach_summary(account,key):
    if not isinstance(key,str) or not 1<=len(key)<=256 or not key.isascii() or any(ord(c)<33 or ord(c)>126 for c in key):
        raise ValueError('OathNet API anahtarını Ayarlar bölümüne girin.')
    account=account.strip()
    if len(account)>254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}",account):
        raise ValueError('Geçerli ASCII e-posta adresi gerekli.')
    local,host=account.rsplit('@',1)
    if local.startswith('.') or local.endswith('.') or '..' in local or '..' in host or any(not label or len(label)>63 or label.startswith('-') or label.endswith('-') for label in host.split('.')):
        raise ValueError('E-posta adresinin biçimi geçersiz.')
    url='https://oathnet.org/api/service/v2/breach/search?'+urlencode({'email[]':account,'wildcard':'false'})
    response=fetch(url,headers={'x-api-key':key,'Accept':'application/json'},redirects=0)
    code=response['status']
    if code==401:
        raise ValueError('OathNet HTTP 401: API anahtarı geçersiz veya yetkisiz.')
    if code==403:
        raise ValueError('OathNet HTTP 403: Plan erişimi veya kota yetersiz; hesap ayarlarını kontrol edin.')
    if code==429:
        raise ValueError('OathNet HTTP 429: Hız/kota sınırı aşıldı. Bekleyin; otomatik yeniden deneme yapılmadı.')
    if code!=200:
        raise ValueError('OathNet HTTP %s: Sorgu tamamlanamadı; kayıt yok sonucu değildir.'%code)
    try:
        payload=json.loads(response['body'])
    except (ValueError,UnicodeError):
        raise ValueError('OathNet geçerli JSON döndürmedi; sonuç bilinmiyor.') from None
    if not isinstance(payload,dict) or payload.get('success') is not True or not isinstance(payload.get('data'),dict):
        raise ValueError('OathNet sorgusu başarılı değil veya yanıt biçimi değişmiş; sonuç bilinmiyor.')
    data=payload['data']
    rows=data.get('items')
    meta=data.get('meta')
    if not isinstance(rows,list) or len(rows)>500 or not isinstance(meta,dict):
        raise ValueError('OathNet sayfa yapısı geçersiz veya 500 kayıt sınırını aşıyor.')
    total=meta.get('total')
    more=meta.get('has_more')
    if type(total) is not int or total<len(rows) or type(more) is not bool or (not rows and (total>0 or more)):
        raise ValueError('OathNet sayfalama bilgisi tutarsız; kayıt yok sonucu üretilemedi.')
    sources=Counter()
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('email'),str) or row['email'].casefold()!=account.casefold():
            raise ValueError('OathNet tam e-posta filtresiyle eşleşmeyen kayıt döndürdü; ham veriler paylaşılmadı.')
        name=row.get('dbname')
        if not isinstance(name,str) or not 1<=len(name)<=300:
            raise ValueError('OathNet kaynak adı eksik veya geçersiz; sonuç bilinmiyor.')
        sources[name]+=1
    # Do not return the original response, rows, cursors, passwords, tokens or hashes.
    return {'source':'OathNet','account':account,'found':bool(rows),'matching_rows_in_page':len(rows),
            'total_rows_reported':total,'has_more':more,
            'breach_sources':[{'database':name,'matching_rows_in_page':count} for name,count in sorted(sources.items())],
            'links':[{'label':'OathNet','url':'https://oathnet.org/'}],
            'note':'Yalnızca ilk sayfanın kaynak/sayı özeti. Daha fazla sayfa otomatik alınmaz; kapsam tam ihlal geçmişi değildir. Sonuç yokluğu güvenlik kanıtı değildir. Ham satırlar, parola, hash ve tokenlar ekrana/vakaya/rapora aktarılmaz.'}
