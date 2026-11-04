"""HIBP v3 direct email search; keys stay server-side, no site scraping."""
import json
import re
from urllib.parse import quote

from .network import fetch

ATTRIBUTION={'source':'Have I Been Pwned',
             'links':[{'label':'Have I Been Pwned','url':'https://haveibeenpwned.com/'}]}


def email_breaches(account,key):
    if not isinstance(key,str) or not re.fullmatch(r'[0-9a-fA-F]{32}',key):
        raise ValueError('HIBP abonelik anahtarınızı Ayarlar bölümüne girin (32 onaltılık karakter).')
    account=account.strip()
    if (len(account)>254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}",account)):
        raise ValueError('Geçerli ASCII e-posta adresi gerekli.')
    local,host=account.rsplit('@',1)
    if local.startswith('.') or local.endswith('.') or '..' in local or '..' in host or any(not label or label.startswith('-') or label.endswith('-') or len(label)>63 for label in host.split('.')):
        raise ValueError('E-posta adresinin biçimi geçersiz.')
    url='https://haveibeenpwned.com/api/v3/breachedaccount/'+quote(account,safe='')+'?truncateResponse=false&includeUnverified=false'
    response=fetch(url,headers={'hibp-api-key':key,'Accept':'application/json'},redirects=0)
    code=response['status']
    if code==404:
        return {**ATTRIBUTION,'account':account,'found':False,'breach_count':0,'breaches':[],
                'note':'HIBP bu sorgu kapsamında kayıt döndürmedi. Bu, hiç ihlal yaşanmadığını veya hesabın güvenli olduğunu kanıtlamaz; hassas/emekli kayıtlar ve doğrulanmamış ihlaller kapsam dışıdır.'}
    if code==401:
        raise ValueError('HIBP HTTP 401: API anahtarı geçersiz veya yetkisiz. Abonelik anahtarını kontrol edin.')
    if code==403:
        raise ValueError('HIBP HTTP 403: Erişim reddedildi. Abonelik yetkisini ve sağlayıcı erişim koşullarını kontrol edin.')
    if code==429:
        delay=response.get('headers',{}).get('retry-after','')
        suffix=(' En az '+str(min(int(delay),86400))+' saniye bekleyin.') if delay.isascii() and delay.isdigit() and len(delay)<=6 else ' Sağlayıcının yeniden deneme süresini bekleyin.'
        raise ValueError('HIBP HTTP 429: Sorgu kotası/hız sınırı aşıldı.'+suffix+' Otomatik yeniden deneme yapılmadı.')
    if code!=200:
        raise ValueError('HIBP HTTP %s: Sorgu tamamlanamadı; bu durum ihlal yok sonucu değildir.'%code)
    try:
        rows=json.loads(response['body'])
    except (ValueError,UnicodeError):
        raise ValueError('HIBP geçerli JSON döndürmedi; sorgu sonucu bilinmiyor.') from None
    if not isinstance(rows,list) or not rows or len(rows)>1000:
        raise ValueError('HIBP yanıt biçimi beklenmiyor; sorgu sonucu bilinmiyor.')
    breaches=[]
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('Name'),str) or not 1<=len(row['Name'])<=200:
            raise ValueError('HIBP ihlal kaydı beklenen biçimde değil; sorgu sonucu bilinmiyor.')
        classes=row.get('DataClasses',[])
        if not isinstance(classes,list) or len(classes)>100 or any(not isinstance(v,str) or len(v)>200 for v in classes):
            raise ValueError('HIBP veri sınıfları beklenen biçimde değil.')
        breach={'name':row['Name'],'data_classes':classes}
        for src,dest in [('Title','title'),('Domain','domain'),('BreachDate','breach_date'),('AddedDate','added_date'),('ModifiedDate','modified_date')]:
            if src in row:
                if not isinstance(row[src],str) or len(row[src])>500:
                    raise ValueError('HIBP ihlal metadatası geçersiz.')
                breach[dest]=row[src]
        for src,dest in [('IsVerified','verified'),('IsFabricated','fabricated'),('IsSpamList','spam_list'),('IsMalware','malware')]:
            if src in row:
                if type(row[src]) is not bool:
                    raise ValueError('HIBP ihlal işaretleri geçersiz.')
                breach[dest]=row[src]
        breaches.append(breach)
    return {**ATTRIBUTION,'account':account,'found':True,'breach_count':len(breaches),'breaches':breaches,
            'note':'HIBP resmi e-posta sorgusu. Doğrulanmamış, hassas ve emekli ihlaller kapsam dışıdır. Yalnızca ihlal metadatası; parolalar veya sızan içerikler alınmaz.'}
