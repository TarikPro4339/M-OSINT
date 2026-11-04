# 111 kart · sürüm 1.0.0 kapsamı

Temiz kurulumda ek paket ve API anahtarı yoktur. HIBP ve OathNet adaptörleri hazırdır; anahtar girilene kadar kartları entegrasyon gerekli görünür.

**45 çalışıyor · 36 kısmi · 30 entegrasyon gerekli**

| No | Özellik | Durum | Gerçek kapsam / gereksinim |
|---:|---|---|---|
| 1 | IP Geolocation | Kısmi kapsam | Anahtarsız ipwho.is üzerinden yaklaşık ülke/şehir/posta kodu/koordinat; alanlar sağlayıcıya bağlıdır, kişi konumu değildir. Ağ izni gerekir. |
| 2 | ASN & ISP Sorgulama | Çalışıyor | Anahtarsız ipwho.is üzerinden ASN ve ISP/kuruluş bilgisi. Sağlayıcı kotası geçerlidir. Ağ izni gerekir. |
| 3 | Ters IP (Reverse IP) Arama | Entegrasyon gerekli | Ters IP sağlayıcısı ve kullanım izni gerekli; arama motoru sonuçları aynı IP kanıtı değildir. |
| 4 | MAC Adresi (OUI) Sorgulama | Entegrasyon gerekli | Güncel, lisanslı IEEE OUI veritabanı veya üretici API adaptörü gerekli. |
| 5 | Port Tarayıcı (Port Scanner) | Kısmi kapsam | Tek genel hedef, en fazla 16 TCP portu ve 4 çalışan. UDP taraması yok. Ağ izni gerekir. |
| 6 | Banner Grabbing | Kısmi kapsam | Yalnızca bağlantı sonrası 512 bayt pasif banner; protokol mesajı veya sürüm doğrulaması yok. Ağ izni gerekir. |
| 7 | VPN / Proxy / Tor Tespiti | Entegrasyon gerekli | Güncel VPN/Proxy/Tor veri sağlayıcısı gerekli; yalnızca ASN verisinden karar verilmez. |
| 8 | Kara Liste (Blacklist / DNSBL) Kontrolü | Entegrasyon gerekli | DNSBL sağlayıcı sözleşmesi, liste seçimi ve sonuç doğrulama adaptörü gerekli. |
| 9 | Traceroute / Ağ Yolu Analizi | Entegrasyon gerekli | İşletim sistemi traceroute adaptörü gerekli; sunucu shell komutu çalıştırmaz. |
| 10 | Ping & Gecikme (Latency) Testi | Kısmi kapsam | TCP bağlantı gecikmesi ölçülür; ICMP ping değil. Ağ izni gerekir. |
| 11 | Alt Ağ (Subnet / CIDR) Hesaplayıcı | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 12 | IPv4 - IPv6 Dönüştürücü ve Çözümleyici | Kısmi kapsam | IP ayrıştırma ve IPv4-mapped gösterimi; gerçek protokol dönüşümü değil. |
| 13 | Shodan / Censys Sorgu Üretici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 14 | BGP Prefix Sorgulama | Entegrasyon gerekli | RIR/BGP kaynak adaptörü gerekli; ASN sahipliği ve zaman damgası doğrulanmalı. |
| 15 | Genel (Public) IP Bilgisi | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 16 | WHOIS Sorgulama | Kısmi kapsam | Yapılandırılmış RDAP kayıt verisi; eski WHOIS protokolü kullanılmaz. Ağ izni gerekir. |
| 17 | DNS Kayıt Analizi | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 18 | Alt Alan Adı (Subdomain) Tespiti | Kısmi kapsam | crt.sh üzerinden pasif sertifika adları; DNS brute force/canlılık yok, 2000 ad sınırı. Ağ izni gerekir. |
| 19 | SSL/TLS Sertifika Analizi | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 20 | HTTP Başlık (Header) Analizi | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 21 | Web Teknoloji Tespiti (Tech Stack) | Kısmi kapsam | HTML/başlık imzaları; doğrulanmış teknoloji envanteri değil. Ağ izni gerekir. |
| 22 | Robots.txt ve Sitemap.xml Okuyucu | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 23 | Wayback Machine Entegrasyonu | Kısmi kapsam | Wayback takvim bağlantısı üretir; snapshot listesi indirilmez. |
| 24 | Cloudflare / WAF Tespiti | Kısmi kapsam | CDN/WAF başlık ve metin ipuçları; kesin tespit değil. Ağ izni gerekir. |
| 25 | Sayfa Kaynağından Link Çıkarıcı | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 26 | Sayfa İçi E-posta ve Telefon Kazıyıcı | Kısmi kapsam | Kamuya açık sayfadan regex adayları; iletişim bilgilerinin sahipliği doğrulanmaz. Ağ izni gerekir. |
| 27 | HTML Yorum Satırı (Comment) Bulucu | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 28 | Favicon Hash (MurmurHash) Hesaplayıcı | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 29 | Yönlendirme (Redirect) Zinciri Takibi | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 30 | Açık Dizin (Directory Listing) Kontrolü | Entegrasyon gerekli | Yetkili güvenlik denetimi entegrasyonu gerekli; hassas .env/.git/backup dosyaları otomatik yoklanmaz. |
| 31 | Çoklu Platform Kullanıcı Adı Tarayıcı | Kısmi kapsam | 55 platform için profil URL üretimi; hesap varlığı taranmaz ve kimlik eşleştirilmez. |
| 32 | GitHub Profil ve Repo Analizi | Kısmi kapsam | GitHub genel profil ve en son güncellenen ilk 30 repo; tam hesap geçmişi değil. Ağ izni gerekir. |
| 33 | GitHub Commit E-posta Çıkarıcı | Entegrasyon gerekli | İzin kapsamı belirlenmiş GitHub commit analizi adaptörü gerekli; kişisel e-posta toplama uygulanmadı. |
| 34 | Gravatar Sorgulama | Kısmi kapsam | E-posta MD5 ve Gravatar bağlantısı; profil varlığı sorgulanmaz. |
| 35 | Discord Snowflake (ID) Çözücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 36 | Discord Davet Kodu Analizi | Kısmi kapsam | Genel davet verisi ve yaklaşık üye sayısı; boost bilgisi sağlayıcı yanıtına bağlı. Ağ izni gerekir. |
| 37 | Steam ID Dönüştürücü | Kısmi kapsam | Steam2/Steam3/Steam64 sayısal dönüşüm; özel URL/profil API analizi yok. |
| 38 | Reddit Kullanıcı Analizi | Entegrasyon gerekli | Reddit erişim politikası/kotasıyla uyumlu OAuth adaptörü gerekli. |
| 39 | Sosyal Medya Bio/Link Ayıklayıcı | Kısmi kapsam | Yapıştırılan HTML içinden Linktree/Beacons/bio.link/lnk.bio; uzaktan profil kazınmaz. |
| 40 | İsimden Kullanıcı Adı (Handle) Türetici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 41 | Wikipedia / Ekşi Sözlük Yazar Kontrolü | Kısmi kapsam | Wikipedia katkı ve Ekşi arama bağlantıları; katkılar indirilmez. |
| 42 | YouTube Kanal ID ve Meta Çıkarıcı | Kısmi kapsam | URL veya yapıştırılan HTML içinden UC kanal ID; tarih/kapak API sorgusu yok. |
| 43 | Telegram Açık Kanal/Grup Ön İzleme | Kısmi kapsam | t.me genel HTML OG metadata; üye sayısı/tüm alanlar garanti değil. Ağ izni gerekir. |
| 44 | Twitch Kanal Bilgisi Sorgulama | Entegrasyon gerekli | Twitch geliştirici uygulaması, OAuth ve Helix adaptörü gerekli. |
| 45 | Keybase / PGP Anahtar Sorgulama | Entegrasyon gerekli | Keybase API ve kriptografik kanıt doğrulama adaptörü gerekli. |
| 46 | E-posta Format ve Sözdizimi Doğrulama | Kısmi kapsam | Pratik ASCII e-posta sözdizimi alt kümesi; RFC kapsamının tamamı veya teslimat doğrulaması yok. |
| 47 | E-posta MX ve Sunucu Kontrolü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 48 | Tek Kullanımlık (Temp Mail) Tespiti | Kısmi kapsam | 5 domainlik örnek temp-mail listesi; güncel ve tam veri tabanı değil. |
| 49 | Kurumsal E-posta Deseni Oluşturucu | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 50 | Veri İhlali (Data Breach) Sorgulama | Entegrasyon gerekli | HIBP resmi breachedaccount API adaptörü hazır. E-posta açık ağ onayıyla HIBP’ye gönderilir; hassas/emekli ve doğrulanmamış ihlaller kapsam dışı. Ayarlar → Have I Been Pwned bölümüne abonelik anahtarı girin. Ağ izni gerekir. |
| 51 | E-posta Başlığı (Mail Header) Analizörü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 52 | Google Hesap / Servis Kontrolü | Entegrasyon gerekli | Google onaylı erişim ve kullanıcı rızası gerekli; gizli hesap varlığı sorgulanmaz. |
| 53 | Telefon Numarası Format Doğrulama (E.164) | Kısmi kapsam | E.164 sözdizimi; etkin hat veya numara tahsisi doğrulanmaz. |
| 54 | Ülke ve Alan Kodu Çözümleyici | Entegrasyon gerekli | requirements-optional.txt kurulmalı. phonenumbers verisinden ülke/bölge tahmini; gerçek konum değil. |
| 55 | Operatör (Carrier) ve Hat Tipi Tespiti | Entegrasyon gerekli | requirements-optional.txt kurulmalı. phonenumbers ilk tahsis operatörü/tipi; numara taşımadan sonraki güncel operatör bilinmez. |
| 56 | Telefon Numarası Saat Dilimi Tahmini | Entegrasyon gerekli | requirements-optional.txt kurulmalı. phonenumbers plan verisinden olası saat dilimleri; gerçek konum/yerel saat doğrulanmaz. |
| 57 | WhatsApp / Telegram Doğrudan Link Üretici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 58 | Telefon Dork Üretici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 59 | Ücretsiz SMS Alım Sitesi Tespiti | Entegrasyon gerekli | Güncel, izinli SMS alım sitesi veri kaynağı gerekli; sonuç yokluğu özel numara kanıtı olmaz. |
| 60 | Skype / Microsoft Hesap Eşleştirme | Entegrasyon gerekli | Microsoft onaylı, kullanıcı rızalı kimlik erişimi gerekli; gizli hesap eşleştirme uygulanmadı. |
| 61 | Görsel EXIF Okuyucu | Entegrasyon gerekli | requirements-optional.txt kurulmalı. Pillow destekli görsel metadata; bazı üreticiye özel alanlar desteklenmeyebilir. |
| 62 | EXIF GPS Koordinat Çözücü | Entegrasyon gerekli | requirements-optional.txt kurulmalı. Pillow EXIF GPS varsa harita bağlantısı; GPS doğruluğu kanıtlanmaz. |
| 63 | PDF Metadata Çıkarıcı | Entegrasyon gerekli | requirements-optional.txt kurulmalı. Belirtilen kapsamda uygulanmıştır. |
| 64 | Office Dokümanları (DOCX/XLSX) Analizi | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 65 | Dosya Hash Hesaplayıcı | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 66 | Dosya İmza (Magic Bytes) Kontrolü | Kısmi kapsam | 9 temel sihirli bayt imzası; tam dosya tipi veya zararsızlık doğrulaması değil. |
| 67 | Strings (Metin) Ayıklayıcı | Kısmi kapsam | ASCII ve UTF-8 adayları; her biri en fazla 1000 sonuç/2000 karakter. |
| 68 | Görselden Metin Okuma (OCR) | Entegrasyon gerekli | Yerel OCR motoru/modeli (ör. Tesseract) adaptörü gerekli; dosya buluta gönderilmez. |
| 69 | Tersine Görsel Arama Link Üretici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 70 | QR Kod ve Barkod Okuyucu | Entegrasyon gerekli | Yerel QR/barkod kütüphanesi adaptörü gerekli; içerik otomatik açılmamalı. |
| 71 | Ses/Video Medya Bilgisi (MediaInfo) | Entegrasyon gerekli | requirements-optional.txt kurulmalı. Mutagen destekli ses/MP4 metadata; tüm video codec/cihazlarını kapsamaz. |
| 72 | Steganografi Temel Kontrolü (LSB/Boyut) | Kısmi kapsam | JPEG/PNG sonuna eklenen baytları bulur; LSB veya genel steganografi tespiti yok. |
| 73 | Favicon İndirici ve Analizörü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 74 | Arşiv (ZIP/RAR) İçerik Listeleme | Kısmi kapsam | ZIP listelenir; RAR adaptörü yok. Sıkıştırma ve girdi limitleri uygulanır. |
| 75 | EXIF Temizleyici (Bonus Savunma Özelliği) | Entegrasyon gerekli | requirements-optional.txt kurulmalı. Belirtilen kapsamda uygulanmıştır. |
| 76 | Base64 / Base32 / Base58 Encode & Decode | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 77 | Hexadecimal (Onaltılık) ve Binary Dönüştürücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 78 | URL ve HTML Entity Encode / Decode | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 79 | ROT13 / Sezar Şifresi Çözücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 80 | JWT (JSON Web Token) Çözücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 81 | Hash Tipi Tanımlayıcı (Hash Identifier) | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 82 | Unix Timestamp Dönüştürücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 83 | Evrensel Regex Ayıklayıcı | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 84 | Zararlı Link Zırhlayıcı (Defang / Refang) | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 85 | Mors Alfabesi ve ASCII Kod Çevirici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 86 | Unicode / Punycode Dönüştürücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 87 | Kripto Cüzdan Format Doğrulayıcı | Kısmi kapsam | BTC Base58Check checksum ve ETH biçimi; Bech32, XMR, ETH checksum yok. |
| 88 | Otomatik Kod Çözücü (Magic Decoder) | Kısmi kapsam | En fazla 5 Base64/Hex katmanı; sezgisel çözüm. |
| 89 | Google Dork Oluşturucu | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 90 | GitHub & GitLab Dork Oluşturucu | Kısmi kapsam | Kendi kuruluşu için repo/dosya arama bağlantıları; sır içeriği çekme, test etme veya kullanma yok. |
| 91 | Pastebin & Kod Paylaşım Sitesi Tarayıcı | Kısmi kapsam | Pastebin için arama motoru bağlantısı; site taraması yok. |
| 92 | Kısaltılmış URL (Short URL) Çözücü | Çalışıyor | Belirtilen kapsamda uygulanmıştır. Ağ izni gerekir. |
| 93 | Açık Wi-Fi / BSSID Konum Sorgulama | Entegrasyon gerekli | BSSID konum sağlayıcısı, açık yetki ve mahremiyet kapsamı gerekli. |
| 94 | Uçuş Kodu ve Gemi (AIS) Sorgu Linkleyici | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 95 | Plaka / Ülke Kodu Rehberi | Kısmi kapsam | 6 ülkelik örnek rehber; tüm ülke/plaka veritabanı değil. |
| 96 | Karanlık Web (Tor / .onion) Durum Kontrolü | Entegrasyon gerekli | Tor/SOCKS taşıma adaptörü gerekli; onion adresleri varsayılan HTTP katmanında engellenir. |
| 97 | User-Agent Havuzu (Rotasyonu) | Entegrasyon gerekli | Kimlik rotasyonu uygulanmadı. Mevcut istemci sabit ve açıklayıcı M-OSINT User-Agent kullanır; engel aşma otomasyonu yok. |
| 98 | Proxy Desteği (HTTP / SOCKS5) | Entegrasyon gerekli | HTTP/SOCKS5 proxy adaptörü ve ayrı güvenlik modeli gerekli; ortam proxy değişkenleri bilerek kullanılmaz. |
| 99 | Çoklu İş Parçacığı (Multi-threading / Async) | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 100 | JSON / CSV / TXT Dışa Aktarma | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 101 | HTML / PDF Rapor Oluşturucu | Kısmi kapsam | HTML rapor ve tarayıcı Yazdır/PDF olarak kaydet; sunucu PDF motoru yok. |
| 102 | Oturum (Case / Workspace) Kaydetme | Çalışıyor | Belirtilen kapsamda uygulanmıştır. |
| 103 | Merkezi API Anahtarı Yöneticisi | Kısmi kapsam | IPinfo Lite, HIBP ve OathNet anahtarlarını yalnızca sunucu belleğinde saklar; genel parola kasası değildir. |
| 104 | Sorgu Geçmişi ve Loglama | Kısmi kapsam | Bellekte son 100 işlem; açık tercihle tarayıcı depolaması. Sunucu sorgu içeriğini günlüğe yazmaz. |
| 105 | Toplu Hedef (Batch) İşleme | Kısmi kapsam | En fazla 20 hedef, yalnızca seçilebilir yerel araçlar; yüzlerce hedef/ağ toplu tarama yok. |
| 106 | URL Takip Parametresi Temizleyici | Çalışıyor | URL bileşenlerini ayrıştırır; utm_*, gclid ve bilinen takip parametrelerini kaldırır. URL ziyaret edilmez. Yerel çalışır; API anahtarı veya ek paket gerekmez. |
| 107 | IOC Listesi Karşılaştırıcı | Çalışıyor | İki satırlık IOC listesinin ortak ve farklı girdilerini bulur. Listeleri ayrı bir --- satırı ile ayırın; harf duyarlı tam eşleşme kullanılır. Yerel çalışır; API anahtarı veya ek paket gerekmez. |
| 108 | E-posta Maskeleyici | Çalışıyor | Metindeki ASCII e-posta adaylarının yerel kısmını maskeler; diğer kişisel verileri anonimleştirmez. Yerel çalışır; API anahtarı veya ek paket gerekmez. |
| 109 | Dosya SHA-256 Doğrulayıcı | Çalışıyor | Seçilen dosyanın SHA-256 özetini girilen güvenilir beklenen özetle karşılaştırır; zararsızlık tespiti yapmaz. Yerel çalışır; API anahtarı veya ek paket gerekmez. |
| 110 | Metin Fark Analizi | Çalışıyor | İki metni satır bazında karşılaştırarak unified diff üretir. Metinleri ayrı bir --- satırı ile ayırın; CRLF/LF ve son satır sonlandırıcısı farkı yok sayılır. Yerel çalışır; API anahtarı veya ek paket gerekmez. |
| 111 | OathNet E-posta İhlal Özeti | Entegrasyon gerekli | Resmi OathNet V2 tek e-posta filtresi; ilk sayfadan yalnızca kaynak adları ve kayıt sayıları. Ham sızıntı/parola/token gösterilmez. Ayarlar → OathNet bölümüne API anahtarı girin. Ağ izni gerekir. |

## Anahtarlar sonrası

Yalnızca HIBP anahtarıyla: 46 çalışan / 36 kısmi / 29 entegrasyon gerekli. Yalnızca OathNet anahtarıyla: 45 çalışan / 37 kısmi / 29 entegrasyon gerekli. Her iki anahtarla: 46 çalışan / 37 kısmi / 28 entegrasyon gerekli. Gerçek anahtar ve plan geçerliliği ilk sorguda denetlenir. IP sorgusu anahtarsız kalır. Ek yerel paketler ayrıca 8 kartı açabilir.
