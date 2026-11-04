"""Original 105 requests and five extra local tools, with explicit coverage."""
import importlib.util
import json
from pathlib import Path

FEATURE_COUNT=len(json.loads((Path(__file__).parent/'features.json').read_text(encoding='utf-8')))
FILE_IDS={28,61,62,63,64,65,66,67,71,72,74,75,109}
NETWORK_IDS={1,2,5,6,10,15,16,17,18,19,20,21,22,24,25,26,27,29,32,36,43,47,50,73,92,111}
OPTIONAL={54:'phonenumbers',55:'phonenumbers',56:'phonenumbers',61:'PIL',62:'PIL',63:'pypdf',71:'mutagen',75:'PIL'}
INTEGRATIONS={
 3:'Ters IP sağlayıcısı ve kullanım izni gerekli; arama motoru sonuçları aynı IP kanıtı değildir.',
 4:'Güncel, lisanslı IEEE OUI veritabanı veya üretici API adaptörü gerekli.',
 7:'Güncel VPN/Proxy/Tor veri sağlayıcısı gerekli; yalnızca ASN verisinden karar verilmez.',
 8:'DNSBL sağlayıcı sözleşmesi, liste seçimi ve sonuç doğrulama adaptörü gerekli.',
 9:'İşletim sistemi traceroute adaptörü gerekli; sunucu shell komutu çalıştırmaz.',
 14:'RIR/BGP kaynak adaptörü gerekli; ASN sahipliği ve zaman damgası doğrulanmalı.',
 30:'Yetkili güvenlik denetimi entegrasyonu gerekli; hassas .env/.git/backup dosyaları otomatik yoklanmaz.',
 33:'İzin kapsamı belirlenmiş GitHub commit analizi adaptörü gerekli; kişisel e-posta toplama uygulanmadı.',
 38:'Reddit erişim politikası/kotasıyla uyumlu OAuth adaptörü gerekli.',
 44:'Twitch geliştirici uygulaması, OAuth ve Helix adaptörü gerekli.',
 45:'Keybase API ve kriptografik kanıt doğrulama adaptörü gerekli.',
 52:'Google onaylı erişim ve kullanıcı rızası gerekli; gizli hesap varlığı sorgulanmaz.',
 59:'Güncel, izinli SMS alım sitesi veri kaynağı gerekli; sonuç yokluğu özel numara kanıtı olmaz.',
 60:'Microsoft onaylı, kullanıcı rızalı kimlik erişimi gerekli; gizli hesap eşleştirme uygulanmadı.',
 68:'Yerel OCR motoru/modeli (ör. Tesseract) adaptörü gerekli; dosya buluta gönderilmez.',
 70:'Yerel QR/barkod kütüphanesi adaptörü gerekli; içerik otomatik açılmamalı.',
 93:'BSSID konum sağlayıcısı, açık yetki ve mahremiyet kapsamı gerekli.',
 96:'Tor/SOCKS taşıma adaptörü gerekli; onion adresleri varsayılan HTTP katmanında engellenir.',
 97:'Kimlik rotasyonu uygulanmadı. Mevcut istemci sabit ve açıklayıcı M-OSINT User-Agent kullanır; engel aşma otomasyonu yok.',
 98:'HTTP/SOCKS5 proxy adaptörü ve ayrı güvenlik modeli gerekli; ortam proxy değişkenleri bilerek kullanılmaz.'
}
PARTIAL={
 1:'Anahtarsız ipwho.is üzerinden yaklaşık ülke/şehir/posta kodu/koordinat; alanlar sağlayıcıya bağlıdır, kişi konumu değildir.',
 5:'Tek genel hedef, en fazla 16 TCP portu ve 4 çalışan. UDP taraması yok.',
 6:'Yalnızca bağlantı sonrası 512 bayt pasif banner; protokol mesajı veya sürüm doğrulaması yok.',
 10:'TCP bağlantı gecikmesi ölçülür; ICMP ping değil.',
 12:'IP ayrıştırma ve IPv4-mapped gösterimi; gerçek protokol dönüşümü değil.',
 16:'Yapılandırılmış RDAP kayıt verisi; eski WHOIS protokolü kullanılmaz.',
 18:'crt.sh üzerinden pasif sertifika adları; DNS brute force/canlılık yok, 2000 ad sınırı.',
 21:'HTML/başlık imzaları; doğrulanmış teknoloji envanteri değil.',
 23:'Wayback takvim bağlantısı üretir; snapshot listesi indirilmez.',
 24:'CDN/WAF başlık ve metin ipuçları; kesin tespit değil.',
 26:'Kamuya açık sayfadan regex adayları; iletişim bilgilerinin sahipliği doğrulanmaz.',
 31:'55 platform için profil URL üretimi; hesap varlığı taranmaz ve kimlik eşleştirilmez.',
 32:'GitHub genel profil ve en son güncellenen ilk 30 repo; tam hesap geçmişi değil.',
 34:'E-posta MD5 ve Gravatar bağlantısı; profil varlığı sorgulanmaz.',
 36:'Genel davet verisi ve yaklaşık üye sayısı; boost bilgisi sağlayıcı yanıtına bağlı.',
 37:'Steam2/Steam3/Steam64 sayısal dönüşüm; özel URL/profil API analizi yok.',
 39:'Yapıştırılan HTML içinden Linktree/Beacons/bio.link/lnk.bio; uzaktan profil kazınmaz.',
 41:'Wikipedia katkı ve Ekşi arama bağlantıları; katkılar indirilmez.',
 42:'URL veya yapıştırılan HTML içinden UC kanal ID; tarih/kapak API sorgusu yok.',
 43:'t.me genel HTML OG metadata; üye sayısı/tüm alanlar garanti değil.',
 46:'Pratik ASCII e-posta sözdizimi alt kümesi; RFC kapsamının tamamı veya teslimat doğrulaması yok.',
 48:'5 domainlik örnek temp-mail listesi; güncel ve tam veri tabanı değil.',
 53:'E.164 sözdizimi; etkin hat veya numara tahsisi doğrulanmaz.',
 54:'phonenumbers verisinden ülke/bölge tahmini; gerçek konum değil.',
 55:'phonenumbers ilk tahsis operatörü/tipi; numara taşımadan sonraki güncel operatör bilinmez.',
 56:'phonenumbers plan verisinden olası saat dilimleri; gerçek konum/yerel saat doğrulanmaz.',
 61:'Pillow destekli görsel metadata; bazı üreticiye özel alanlar desteklenmeyebilir.',
 62:'Pillow EXIF GPS varsa harita bağlantısı; GPS doğruluğu kanıtlanmaz.',
 66:'9 temel sihirli bayt imzası; tam dosya tipi veya zararsızlık doğrulaması değil.',
 67:'ASCII ve UTF-8 adayları; her biri en fazla 1000 sonuç/2000 karakter.',
 71:'Mutagen destekli ses/MP4 metadata; tüm video codec/cihazlarını kapsamaz.',
 72:'JPEG/PNG sonuna eklenen baytları bulur; LSB veya genel steganografi tespiti yok.',
 74:'ZIP listelenir; RAR adaptörü yok. Sıkıştırma ve girdi limitleri uygulanır.',
 87:'BTC Base58Check checksum ve ETH biçimi; Bech32, XMR, ETH checksum yok.',
 88:'En fazla 5 Base64/Hex katmanı; sezgisel çözüm.',
 90:'Kendi kuruluşu için repo/dosya arama bağlantıları; sır içeriği çekme, test etme veya kullanma yok.',
 91:'Pastebin için arama motoru bağlantısı; site taraması yok.',
 95:'6 ülkelik örnek rehber; tüm ülke/plaka veritabanı değil.',
 101:'HTML rapor ve tarayıcı Yazdır/PDF olarak kaydet; sunucu PDF motoru yok.',
 103:'IPinfo Lite, HIBP ve OathNet anahtarlarını yalnızca sunucu belleğinde saklar; genel parola kasası değildir.',
 104:'Bellekte son 100 işlem; açık tercihle tarayıcı depolaması. Sunucu sorgu içeriğini günlüğe yazmaz.',
 105:'En fazla 20 hedef, yalnızca seçilebilir yerel araçlar; yüzlerce hedef/ağ toplu tarama yok.'
}


def catalog(keys=None):
    rows=json.loads((Path(__file__).parent/'features.json').read_text(encoding='utf-8'))
    keys=keys or {}
    for r in rows:
        n=r['id']
        r.update(status='partial' if n in PARTIAL else 'functional', network=n in NETWORK_IDS,
                 kind='file' if n in FILE_IDS else 'system' if 99<=n<=105 else 'text',
                 note=PARTIAL.get(n, 'Belirtilen kapsamda uygulanmıştır.'), requirement=None, runnable=True)
        if n in INTEGRATIONS:
            r.update(status='integration',note=INTEGRATIONS[n],runnable=False,requirement='Sağlayıcı / adaptör')
        if n in OPTIONAL and importlib.util.find_spec(OPTIONAL[n]) is None:
            r.update(status='integration',requirement='Ek paket: '+OPTIONAL[n],runnable=False,
                     note='requirements-optional.txt kurulmalı. '+PARTIAL.get(n,r['note']))
        if n==2:
            r['note']='Anahtarsız ipwho.is üzerinden ASN ve ISP/kuruluş bilgisi. Sağlayıcı kotası geçerlidir.'
        if n==50:
            configured=bool(keys.get('hibp'))
            r.update(status='functional' if configured else 'integration',runnable=configured,
                     requirement=None if configured else 'HIBP abonelik anahtarı',
                     note='HIBP resmi breachedaccount API adaptörü hazır. E-posta açık ağ onayıyla HIBP’ye gönderilir; hassas/emekli ve doğrulanmamış ihlaller kapsam dışı. '+('Anahtar yapılandırıldı; geçerliliği ilk sorguda denetlenir.' if configured else 'Ayarlar → Have I Been Pwned bölümüne abonelik anahtarı girin.'))
        if n in (1,2) and keys.get('ipinfo'):
            r['note']='İsteğe bağlı IPinfo Lite seçili; ülke ve ASN/kuruluş verisi. Şehir/koordinat yok. Anahtarı silerek anahtarsız ipwho.is sağlayıcısına dönün.'
        if 106<=n<=110:
            r['note']=r['description']+' Yerel çalışır; API anahtarı veya ek paket gerekmez.'
        if n==111:
            configured=bool(keys.get('oathnet'))
            r.update(status='partial' if configured else 'integration',runnable=configured,
                     requirement=None if configured else 'OathNet API anahtarı / plan erişimi',
                     note='Resmi OathNet V2 tek e-posta filtresi; ilk sayfadan yalnızca kaynak adları ve kayıt sayıları. Ham sızıntı/parola/token gösterilmez. '+('Anahtar yapılandırıldı; geçerliliği ilk sorguda denetlenir.' if configured else 'Ayarlar → OathNet bölümüne API anahtarı girin.'))
    return rows
