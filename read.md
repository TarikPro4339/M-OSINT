# M-OSINT v1.0.0

**Yapımcı: TarikPro43391**

M-OSINT, Windows'ta `M-OSINT.bat` ile başlatılan, yerel çalışan bir açık kaynak araştırma panelidir. Terminal temalı arayüzü ve fsociety esintili, atlanabilir ASCII giriş animasyonu bulunur.

## Hızlı kurulum

1. Proje ZIP'ini tamamen bir klasöre çıkarın.
2. Python **3.10 veya üzeri** kurulu olmalı. Windows kurulumunda **Add Python to PATH** seçeneğini işaretleyin.
3. `M-OSINT.bat` dosyasına çift tıklayın.
4. Panel tarayıcıda `http://127.0.0.1:8765` adresinde açılır.
5. Sunucuyu kapatmak için terminalde **Ctrl+C** kullanın. Yalnızca tarayıcıyı kapatmak sunucuyu durdurmaz.

Çekirdek uygulama ek Python paketi veya yönetici yetkisi istemez. İnternet kullanan sorgular ayrıca ağ onayı gerektirir.

Port doluysa proje klasöründeki terminalden farklı port seçebilirsiniz:

```bat
M-OSINT.bat --port 8766
```

Elle başlatmak için:

```bat
py -3 run.py
```

## Araçlar ve kapsam

Katalogda **111 kart** bulunur. Ek paket ve API anahtarı olmayan kurulumda:

| Durum | Sayı | Açıklama |
|---|---:|---|
| Çalışıyor | 45 | Kartta belirtilen kapsamda uygulanmış işlev |
| Kısmi kapsam | 36 | Sınırları açıklanmış analiz veya bağlantı üretimi |
| Entegrasyon gerekli | 30 | Anahtar, ek paket ya da henüz uygulanmamış adaptör gerekir |

Kart sayısı, 111 tam uygulanmış özellik anlamına gelmez. Her aracın açıklamasını ve kapsam notunu okuyun. Anahtar veya ek paket eklendiğinde bazı kartların durumu değişir.

Başlıca araçlar:

- IP/ASN, DNS, RDAP, TLS ve HTTP başlık analizi.
- CIDR hesaplama, Snowflake ve Steam ID çözümleme.
- Base64/32/58, Hex/Binary, URL/HTML, JWT, zaman damgası ve IOC araçları.
- Dosya özetleri, ZIP içerik listesi ve Office metadata analizi.
- URL takip parametresi temizleme, IOC listesi karşılaştırma, e-posta maskeleme, dosya SHA-256 doğrulama ve metin farkı analizi.
- Vaka kaydetme/açma ve JSON, CSV, TXT, HTML rapor dışa aktarma. PDF için **Yazdır / PDF** kullanılır.

## IP, HIBP ve OathNet

**IP ve ASN sorgusu:** Varsayılan sağlayıcıyla API anahtarı gerekmez. İnternet erişimi ve sağlayıcı kotası geçerlidir. Konum bilgisi yaklaşık ağ konumudur; kişi veya ev adresi değildir. IPinfo Lite yalnızca isteğe bağlı alternatif sağlayıcıdır.

**#50 Have I Been Pwned:** `Ayarlar & bağlantılar → Have I Been Pwned` bölümüne HIBP abonelik anahtarınızı girin. E-posta sorgusunda ihlal adları, tarihler ve etkilenen veri türleri gösterilir. Hassas, emekli ve doğrulanmamış ihlaller bu sorgunun kapsamı dışındadır. Hata veya kota aşımı “ihlal yok” olarak gösterilmez.

**#111 OathNet:** `Ayarlar & bağlantılar → OathNet` bölümüne OathNet API anahtarınızı girin. Uygun plan ve kota gerekir. Tek e-posta için ilk sayfanın kaynak adları ve sayıları özetlenir. Ham sızıntı satırları, parolalar, hash ve tokenlar sonuçlara, vakaya veya rapora aktarılmaz.

Anahtarlar bağımsızdır ve yalnızca sunucu belleğinde tutulur. Sunucuyu yeniden başlatınca tekrar girmeniz gerekir. HIBP/OathNet sorgularında tam e-posta adresinin sağlayıcıya gönderilmesi için her çalıştırmada ağ onayı alınır.

## İsteğe bağlı paketler

EXIF/GPS ve görsel temizleme, PDF metadata, ayrıntılı telefon planı ve medya metadata araçları için:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
M-OSINT.bat
```

Bu paketler çekirdeği açmak için gerekli değildir. Kurulum internet erişimi gerektirir. OCR ve QR/barkod adaptörleri bu paketle uygulanmış hâle gelmez.

## Vaka ve gizlilik

Sonuçlar varsayılan olarak sekme belleğinde tutulur; yenilemeden veya kapatmadan önce **Vakayı kaydet** kullanın. **Bu tarayıcıda hatırla** seçeneği verileri tarayıcının yerel depolamasına, şifresiz kaydeder.

Sunucu yalnızca `127.0.0.1` üzerinde çalışır; port yönlendirmesiyle internete açmayın. Ağ sorguları onaya bağlıdır. Aktif TCP testi için hedef üzerindeki yetkinizi ayrıca onaylamanız gerekir.

Araştırmaları yalnızca yetkili olduğunuz kapsamda yapın. Hesap bağlantıları sahiplik kanıtı, sonuç bulunamaması da güvenlik kanıtı değildir.

## Sorun giderme

- **Python bulunamadı:** Python'u kurun ve PATH ayarını kontrol edin.
- **Panel açılmadı:** Terminaldeki mesajı okuyun; ZIP'in tamamını çıkardığınızdan emin olun.
- **Port kullanılıyor:** `--port 8766` gibi farklı bir port deneyin.
- **Entegrasyon gerekli:** Kartın istediği anahtar, paket veya adaptörü kontrol edin.
- **401/403/429:** Anahtarı, plan erişimini ve sağlayıcı kotasını kontrol edin.
- **DNS/bağlantı hatası:** İnternet, DNS erişimi ve hedefi kontrol edin; bunu boş sonuç saymayın.

Ayrıntılı kurulum için `README.md`, numaralı kapsam için `docs/FEATURES.md`, doğrulama sınırları için `docs/VALIDATION.md` dosyasını okuyun. Gerçek anahtarlarla canlı HIBP/OathNet doğrulaması yapılmış olduğu iddia edilmez.

## Sürüm ve lisans

**Sürüm: v1.0.0 · Yapımcı: TarikPro43391**

Kullanıcı açıkça istemedikçe sürüm numarası değiştirilmez. Projenin MIT lisansı `LICENSE` dosyasındadır; verilen ASCII çiziminin atıfları korunmuştur.
