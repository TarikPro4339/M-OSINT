# M-OSINT 1.0.0 · Yerel araştırma paneli

**Windows'ta `M-OSINT.bat` ile açılan, fsociety esintili terminal intro ve web tabanlı OSINT çalışma alanı.**

**Sürüm politikası:** Kullanıcı açıkça istemedikçe sürüm numarası **v1.0.0** olarak kalır.

Özgün M-OSINT v0.0.8 projesinin modüler, bağımlılıksız çekirdekle yeniden düzenlenmiş sürümüdür. Yapımcı: **TarikPro43391**. MIT lisansı korunmuştur. Verilen `fsociety.ascii` değiştirilmeden kullanılmıştır; çizimdeki XER0 atfı korunur.

## Başlatma · Windows

1. ZIP'i **tamamen çıkarın**. ZIP önizlemesi içinden çalıştırmayın.
2. [python.org](https://www.python.org/downloads/) üzerinden Python **3.10 veya üzeri** kurulu olmalı. Kurulumda **Add Python to PATH** seçeneğini açın. Desteklenen güncel bir Python sürümü önerilir.
3. `M-OSINT.bat` dosyasına çift tıklayın. Yönetici yetkisi gerekmez; çekirdek paket indirmez.
4. Sunucu bağlandıktan sonra tarayıcı `http://127.0.0.1:8765` adresinde açılır.
5. Durdurmak için açık terminalde **Ctrl+C** kullanın. Tarayıcıyı kapatmak sunucuyu durdurmaz.

Port doluysa başlatıcı başka hizmeti açmaz; hata mesajı gösterir. Farklı port:

```bat
M-OSINT.bat --port 8766
```

Manuel başlatma (Windows/macOS/Linux):

```text
python run.py
python run.py --no-browser --port 8766
```

`python` komutunuz yoksa Windows'ta `py -3` kullanın. `static/index.html` dosyasını doğrudan açmayın; API için yerel sunucu gerekir. Windows başlatıcısı varsa önce `.venv` Python'unu, sonra `py -3`, sonra `python` komutunu kullanır.

## 111 kart · 105 istek + 5 yerel araç + OathNet

**Panelde özgün 105 istek ve 5 yeni yerel araç için toplam 111 kart vardır; hepsinin tam uygulanmış olduğu iddia edilmez.** Her kart, özgün isteği ve bu sürümün gerçek kapsamını ayrı ayrı gösterir.

| Temiz çekirdek kurulumu | Sayı | Anlamı |
|---|---:|---|
| Çalışıyor | 45 | Belirtilen kapsamda uygulanmış araç veya çalışma alanı işlevi |
| Kısmi kapsam | 36 | Çalışır; isteğin bazı bölümleri sınırlı, bağlantı üretimi veya sezgisel analiz |
| Entegrasyon gerekli | 30 | Çalıştırılmaz; gereken paket, anahtar, sağlayıcı veya adaptör açıkça yazılır |

IP ve ASN sorgusu ilk açılıştan itibaren **token/hesap gerektirmeden** ipwho.is üzerinden çalışır. 8 ek paketli araç, isteğe bağlı paketler kurulunca açılır. #50 HIBP e-posta ihlal adaptörü hazırdır; HIBP abonelik anahtarı yapılandırıldığında açılır. Sayaçlar kurulu pakete göre otomatik değişir. **“Çalışıyor” canlı sağlayıcının o anda erişilebilir olduğu veya kota sorunu olmadığı anlamına gelmez.** Sağlayıcı hatası ayrı hata olarak döner.

Tam numaralı kapsam tablosu: [docs/FEATURES.md](docs/FEATURES.md). Özgün liste: [docs/requested-features.txt](docs/requested-features.txt).

Örnekler:

- Yerel: IPv4/IPv6 ve CIDR, Snowflake, Steam ID, Base64/32/58, Hex/Binary, URL/HTML, ROT13/Sezar, JWT, hash tanıma, zaman damgası, IOC, defang, Mors, IDNA, dosya hash/strings, ZIP/Office metadata.
- İzinli ağ: Google DoH ile DNS, RDAP kayıt verisi, crt.sh pasif adları, TLS, HTTP başlıkları, link/yorum çıkarma, robots/sitemap, GitHub genel profil, Discord genel davet, Telegram genel önizleme, anahtarsız ipwho.is IP/ASN sorgusu.
- Sınırlı aktif test: tek genel hedef için en fazla 16 TCP portu, 4 çalışan; ayrı yetki onayı. UDP, ICMP, protokol yoklaması, exploit yok.
- Açıkça kısmi: 55 profil bağlantısı **hesap varlığı taraması değildir**; Wayback ve bazı sosyal/arama araçları bağlantı üretir. Temp-mail ve ülke rehberi küçük örnek listeler kullanır.
- Devre dışı: özel hesap eşleştirme, BSSID konum, hassas dosya yoklama, Tor, proxy ve kimlik rotasyonu; gerekli adaptör ve kapsam tanımlanmadan sonuç üretmez.

## İlk araştırma

1. **Araçları keşfet** → ad/numara ile ara veya kategori seç.
2. Bir kartı aç; **gerçek kapsam** açıklamasını oku.
3. Yerel araçta girdiyi/dosyayı seç ve **Analizi çalıştır** düğmesini kullan.
4. Ağ aracında hedefin dış sunucuya gönderileceğini onayla. TCP testinde ayrıca hedef üzerindeki yetkini onayla.
5. Sonuç, kapsam ve UTC zaman damgasıyla oturum vakasına eklenir. Hatalar başarı veya “bulunamadı” gibi gösterilmez.
6. **Vaka & rapor** ekranında sonuçları incele, tek tek kaldır, JSON/CSV/TXT/HTML dışa aktar veya **Yazdır / PDF** ile tarayıcıdan PDF olarak kaydet.

JWT imzası doğrulanmaz. IP/telefon konumları kişi konumu kanıtı değildir. Aynı kullanıcı adı aynı kişi demek değildir. Numara operatör bilgisi ilk tahsis planıdır; taşınmış numarada güncel operatörü vermez.

## Ek yerel analiz paketleri · isteğe bağlı

Çekirdeği kullanmak için bu adım gerekli değildir. EXIF/GPS/temizleme için Pillow, PDF metadata için pypdf, telefon planı için phonenumbers, ses/MP4 metadata için mutagen:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
M-OSINT.bat
```

macOS/Linux:

```text
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-optional.txt
.venv/bin/python run.py
```

Paket kurulumu PyPI erişimi gerektirir. Paketlerin desteklediği bir Python sürümü kullanın; bir sürüm için hazır paket yoksa desteklenen kararlı Python ile yeni sanal ortam oluşturun. Paketler aralıkla sınırlandırılmıştır; tam kilitlenmiş/offline dağıtım değildir. Kurulumdan sonra sunucuyu yeniden başlatın. OCR ve QR/barkod bu pakette uygulanmış değildir.

Görsel temizleyici kaynak görseli değiştirmez; yalnızca piksellerden yeni PNG üretir. EXIF, ICC ve PNG metin alanları taşınmaz; animasyon kaybolur. Görüntünün kendi içeriğindeki konum/yüz/yazılar kaldırılmaz. Temizlenmiş dosyayı analiz penceresindeki düğmeden ayrıca indirin; vaka içine dosya baytları kaydedilmez.

## Anahtarlar ve ağ kaynakları

**IP sorgusu için API anahtarı veya üyelik gerekmez.** IP Geolocation (#1) ve ASN/ISP (#2) kartlarını açıp genel IP adresini girin, ağ iznini onaylayın ve çalıştırın. Varsayılan sağlayıcı `https://ipwho.is/` üzerinden ülke/şehir/posta kodu/koordinat ve ASN/ISP verisi alınır. Alanlar sağlayıcıya göre eksik olabilir; konum yaklaşık ağ konumudur. Sağlayıcının ücretsiz kotası ve erişim koşulları geçerlidir; kota/hata durumu sonuç gibi gösterilmez.

Ayarlar bölümündeki **IPinfo Lite anahtarı tamamen isteğe bağlı alternatif** içindir; sorguyu açmak için girilmez. Girerseniz yalnızca ülke/ASN sağlayan IPinfo seçilir. **Anahtarsız sağlayıcıya dön** düğmesi anahtarı siler. Anahtar yalnızca süreç belleğinde tutulur; sunucu kapanınca ipwho.is varsayılanına dönülür. Shodan/VirusTotal kasası değildir. HIBP için aşağıdaki ayrı bellek ayarı kullanılır.

| İşlem | Verinin gönderildiği yer |
|---|---|
| DNS/MX | `dns.google` (Google Public DNS); domain ve kayıt tipi |
| RDAP | `rdap.org` ve yönlendirdiği genel kayıt servisi; domain |
| Sertifika adları | `crt.sh`; domain |
| IP/ASN (varsayılan) | `ipwho.is`; genel IP, anahtar yok |
| IP/ASN (isteğe bağlı alternatif) | `api.ipinfo.io`; IP, yalnızca kullanıcı alternatif anahtarı girdiyse Authorization başlığı |
| Kendi genel IP'n | `api.ipify.org`; bağlantının çıkış IP'si |
| OathNet e-posta özeti | `oathnet.org`; tam e-posta filtresi, `x-api-key` başlığında API anahtarı |
| HIBP e-posta ihlali | `haveibeenpwned.com`; tam e-posta adresi, `hibp-api-key` başlığında abonelik anahtarı |
| GitHub | `api.github.com`; genel kullanıcı adı |
| Discord | `discord.com`; genel davet kodu |
| Telegram | `t.me`; genel kanal adı |
| Web/TLS/TCP | Girdiğin genel hedef ve izinli yönlendirme hedefleri |

Yerel araçlar dış ağ isteği yapmaz. Üretilen bağlantılara **sen tıklayınca** ilgili siteye gidersin; tarayıcı gezintisi sunucunun genel-IP filtresinden geçmez. Panel dış sitelerin içeriklerini gömmez, otomatik olarak açmaz veya çalıştırmaz. Sağlayıcı koşulları, erişim politikaları ve kotaları geçerlidir. Sabit, açıklayıcı User-Agent kullanılır.

## Vaka, mahremiyet ve sınırlar

- Varsayılan vaka/geçmiş **sekme belleğinde** tutulur. Yenileme veya sekmeyi kapatma bunları kaybettirir. Kaydetmek için **Vakayı kaydet** kullanın.
- **Bu tarayıcıda hatırla** tercihiyle vaka ve son 100 işlem localStorage'a yazılır; şifreli değildir. Başka sekmeler eşzamanlı düzenleme yapmaz; son kaydedenin kopyası geçerli olur.
- **Kaydedilen verileri sil**, localStorage kopyasını kaldırır. Açık sekme belleğindeki vaka ayrıca Vaka ekranından temizlenir. İndirilen raporları/JSON dosyalarını silmez.
- Sunucu sorgu geçmişini diske yazmaz. Geçmişte yalnızca araç/zaman/durum tutulur; girdi ve sonuçlar vaka kaydındadır. API anahtarları vaka/rapor dışa aktarmasına dahil edilmez.
- Son 100 sonuç, toplam yaklaşık 6 MiB vaka sınırı. Tek sonuç vaka içinde serileştirilmiş boyut sınırına uygun bir önizlemeyle kısaltılır; büyük tam çıktı analiz penceresinde kalır. Yeni sonuç eklemek eski sonuçları düşürebilir; önemli vakaları zamanında dışa aktarın.
- Dosya: 8 MiB; JSON istek: 12 MiB; HTTP yanıt: 1 MiB; metin: 100.000 karakter; dosya adı/metadata güvenilmeyen veri olarak işlenir.
- Base58 büyük tam sayı işlemleri için ek sınır: 4096 girdi baytı / 5600 kodlanmış karakter.
- ZIP: en fazla 2000 girdi, toplam 64 MiB açılmış boyut, girdi başına 8 MiB, en fazla 200:1 sıkıştırma oranı. Arşivler diske çıkarılmaz. RAR desteklenmez.
- Görsel: en fazla 16 megapiksel. PDF/görsel/medya parser'ları tek kullanıcı yerel kullanım içindir; düşmanca dosya analizi için işletim sistemi izolasyonunun yerini tutmaz.
- Toplu hedef: yalnızca seçilebilir **yerel araçlar**, en fazla 20 satır. .txt yüklenebilir. Ağ toplu taraması uygulanmadı.

## Güvenli varsayılanlar

Sunucu yalnızca **127.0.0.1** üzerinde dinler. Host ve Origin denetimi, her başlangıçta rastgele istek anahtarı, JSON zorunluluğu, istek/bağlantı/eşzamanlılık sınırları, CSP ve güvenli çıktı gösterimi vardır. HTTP taşıyıcısı DNS'teki tüm adresleri denetler, bağlantıyı doğrulanan IP'ye sabitler ve TLS'te özgün alan adını doğrular. Her yönlendirme yeniden denetlenir; iç ağ, loopback, link-local, IPv6 geçiş adresleri, URL içi kullanıcı bilgileri, 80/443 dışı web portları ve HTTPS→HTTP düşürme engellenir. Ortam proxy ayarları okunmaz.

Bu, tek kullanıcı yerel geliştirme/araştırma uygulamasıdır; internete açık üretim sunucusu veya çok kullanıcılı kimlik sistemi değildir. Port yönlendirmesiyle yayımlamayın. Yerel aynı kullanıcı süreçlerine veya tarayıcı eklentilerine karşı bir güvenlik sınırı oluşturmaz. Ayrıntılar: [docs/SECURITY.md](docs/SECURITY.md).

## Test

Çekirdek testler ek paket veya dış servis gerektirmez:

```text
python -m unittest discover -s tests -v
```

Gerçek loopback HTTP testleri de çalışır; işletim sisteminin yerel bağlantılara izin vermesi gerekir. Test raporu ve dış servis doğrulama sınırları: [docs/VALIDATION.md](docs/VALIDATION.md).

## Proje yapısı

```text
M-OSINT.bat               Windows başlatıcısı
run.py                    Sunucu ve tarayıcı başlangıcı
mosint/server.py          Yerel API, izinler ve sınırlar
mosint/network.py         Genel IP denetimli, IP sabitlemeli taşıma
mosint/tools.py           Yerel/dosya/ağ araçları
mosint/extra_tools.py     Beş ek yerel araştırma aracı
mosint/hibp.py            Resmi HIBP e-posta ihlal adaptörü
mosint/oathnet.py         Resmi OathNet kaynak/sayı özeti
mosint/catalog.py         Durumlar ve kapsam açıklamaları
mosint/features.json      105 istek + 5 yerel araç + OathNet kataloğu
static/                   Arayüz, intro ve verilen ASCII
tests/                    Birim ve HTTP güvenlik testleri
docs/                     Kapsam, kaynaklar, doğrulama ve geçiş notları
```

Önceki sürümden geçiş ve düzeltilen yanlış ihlal yorumu: [docs/MIGRATION.md](docs/MIGRATION.md). Sağlayıcı belgeleri: [docs/SOURCES.md](docs/SOURCES.md).

## Son eklenen 5 araç · #106–110

Sürüm **v1.0.0**, yapımcı **TarikPro43391**. Beşi de yereldir; internet, ek paket ve API anahtarı gerekmez. Araç kütüphanesinde bulunur.

1. **URL Takip Parametresi Temizleyici:** Tam HTTP/HTTPS URL girin. Bilinen takip parametreleri kaldırılır; adres ziyaret edilmez. İmzalı URL değişince geçersiz olabilir.
2. **IOC Listesi Karşılaştırıcı:** Listeleri ayrı bir `---` satırıyla ayırın. Ortak, yalnızca ilk ve yalnızca ikinci listedeki girdiler gösterilir. Harf duyarlı tam metin eşleşmesi; her liste en fazla 2000 satır.
3. **E-posta Maskeleyici:** Metni yapıştırın; ASCII adresler `a***@example.com` biçiminde maskelenir. Bütün kişisel verileri anonimleştirmez.
4. **Dosya SHA-256 Doğrulayıcı:** Güvenilir kaynaktaki 64 karakterlik beklenen özeti girip dosyayı seçin. Özet eşleşmesi gösterilir; dosyanın zararsız olduğu söylenmez. En fazla 8 MiB.
5. **Metin Fark Analizi:** Metinleri ayrı bir `---` satırıyla ayırın. Satır bazında unified diff gösterilir. Her metin en fazla 1000 satır; CRLF/LF ve son satır sonlandırıcısı farkı karşılaştırılmaz.

## HIBP e-posta ihlali · #50

**Ayarlar & bağlantılar → Have I Been Pwned** bölümüne [HIBP abonelik anahtarınızı](https://haveibeenpwned.com/API/Key) girin. Resmi e-posta API’si için bu anahtar gerekir; IP sorgusu anahtarsız kalır. Anahtar 32 onaltılık karakterdir ve yalnızca sunucu belleğinde tutulur. Sunucuyu yeniden başlatınca yeniden girilmelidir; anahtar rapora, vaka dosyasına veya günlüğe dahil edilmez. HIBP ve IPinfo ayarları birbirini silmez.

**#50 Veri İhlali Sorgulama** kartını açın, araştırmaya yetkili olduğunuz ASCII e-posta adresini girin ve tam adresin HIBP’ye gönderilmesi için ağ iznini onaylayın. Sonuçta ihlal adları, tarihleri, veri sınıfları ve doğrulama işaretleri gösterilir. E-posta ve sonuçlar yerel oturum vakasına eklenir; kalıcı depolama tercihiniz geçerlidir.

404 yalnızca HIBP’nin bu kapsamda kayıt döndürmediği anlamına gelir; güvenli hesap kanıtı değildir. 401/403/429 ve bozuk yanıtlar hata olarak görünür. Otomatik yeniden deneme veya gizli veri kazıma yapılmaz. Sorgu doğrulanmamış ihlalleri dışlar; HIBP’nin hassas/emekli kayıtları bu uç noktada dönmez. Sızan parola veya içerik indirilmez. Resmi kaynak: [Have I Been Pwned API v3](https://haveibeenpwned.com/API/v3).

## OathNet · #111 E-posta İhlal Özeti

**Ayarlar & bağlantılar → OathNet** bölümüne hesabınızdaki API anahtarını girin. Uygun plan ve kota gerekir. Anahtar yalnızca sunucu belleğinde tutulur; HIBP/IPinfo ayarını değiştirmez. Sunucu yeniden başlayınca silinir.

#111 kartında araştırmaya yetkili olduğunuz ASCII e-posta adresini girin ve OathNet’e gönderim için ağ iznini onaylayın. Resmi V2 breach/search uç noktasında tek tam e-posta filtresi kullanılır. İlk sayfadan yalnızca kaynak adları ve sayılar özetlenir. Daha fazla sayfa varsa belirtilir; otomatik sayfalama, toplu arama veya stealer/victim dosyası indirme yoktur.

Sağlayıcı yanıtı ham veri içerebilir; uygulama yalnızca kaynak/sayı alanlarını çıkarır. Parola, hash, token ve diğer ham satırlar ekrana, vakaya veya rapora aktarılmaz. 401/403/429, 404 veya bozuk yanıt temiz sonuç sayılmaz. Başarılı boş sonuç da tam ihlal yokluğu/güvenlik kanıtı değildir. Kaynak: [OathNet kimlik doğrulama](https://docs.oathnet.org/introduction/authentication), [ihlal arama rehberi](https://docs.oathnet.org/guides/breach-search).

## Son hata kontrolleri

Analiz bitmeden vaka değiştirme/temizleme ve eşzamanlı anahtar güncellemeleri engellenir. Anahtar kaydedilip katalog yenilemesi başarısız olursa panel bunu açıkça bildirir. Eksik HTTP yanıtları reddedilir. İlk IP erişilemezse yalnızca önceden doğrulanmış genel IP alternatifleri sınırlı olarak denenir; TLS sertifika hatası aşılmaz. Güncel doğrulama raporu `docs/VALIDATION.md` içindedir. Sürüm v1.0.0, yapımcı TarikPro43391.
