# v1.0.0 · Hata kontrolü

Sürüm kullanıcı isteğiyle **1.0.0** olarak sabittir. Kullanıcı açıkça istemedikçe sürüm numarası değiştirilmez. Anahtarsız IP/ASN sorgusu korunur; IPinfo yalnızca isteğe bağlı alternatiftir.

## Düzeltilen hatalar

- `::/128`, `::/127` ve `::/126` gibi düşük sayısal IPv6 ağlarının ilk/son adresleri yanlışlıkla IPv4 biçimine dönüşebiliyordu. Adres ailesi korunur.
- Büyük, çok sayıda tırnak/ters eğik çizgi içeren bir sonuç önizlemesi tekrar JSON'a çevrilince içe aktarma limitini aşabiliyordu. Kaydedilen önizleme artık tekrar açılabilir sınırda tutulur; kaynak sonuç değiştirilmez.
- Dosya okunurken ikinci tıklama ikinci analizi başlatabiliyordu. İşlem kilidi ilk asenkron okumadan önce alınır; okuma hatasında da serbest bırakılır.
- ASCII dışı yerel oturum başlığı bağlantıyı cevapsız kapatabiliyordu. Artık JSON 403 hatası döner. Bu, kullanıcının girmesi gereken sağlayıcı tokenı değildir; panelin otomatik yerel istek korumasıdır.
- DNS çözümleme hataları anlaşılır bağlantı/DNS mesajı verir.
- Arayüz ve HTML/PDF rapor sürümü sunucudaki tek sürüm bilgisinden alınır. Başlangıç HTML'i, API, belgeler ve paket adı v1.0.0 olarak eşitlendi.

## Başarılı doğrulama

**98 Python testi ve 19 JavaScript kontrolü, toplam 117 kontrol geçti.**

| Grup | Sayı | Doğrulama |
|---|---:|---|
| Yerel/dosya/ağ politikası | 41 | Bilinen vektörler, IPv6 uçları, hash/kodlama, ZIP/XML, IP sabitleme ve yönlendirme kuralları |
| Anahtarsız IP | 9 | Anahtarsız istek ve API yönlendirmesi, hata/eksik veri, genel IP ve ağ onayı, isteğe bağlı IPinfo |
| Bellekte HTTP işleyicisi | 14 | Gerçek HTTP parser ve uygulama handler'ı; Host/Origin/oturum, boyut/iş sınırları, statik izin listesi, sürüm eşleşmesi |
| Arayüz işlevleri | 19 | Rapor sürümü/yapımcı, #110 vaka, büyük vaka, dosya baytlarını kaydetmeme, çift gönderim/kilit, HIBP anahtarını ekleme/silme |
| OathNet adaptörü | 11 | Tam e-posta filtresi, gizli veri ayıklama, sayfalama/şema hataları, HTTP hataları, API yönlendirmesi ve bağımsız anahtarlar |
| HIBP resmi adaptörü | 12 | URL kodlama, anahtar başlığı, 200/404/401/403/429/500, bozuk yanıt, ağ onayı ve bağımsız anahtar ayarları |
| Beş yeni yerel araç | 11 | #106–110 gerçek sonuçları, sınırlar, hatalı girdiler, API yönlendirmesi, sürüm ve yapımcı |

Python ortamı Windows / Python 3.15.2. JavaScript kontrolleri Node VM ve küçük DOM test nesneleriyle gerçek uygulama fonksiyonlarını çalıştırır; tarayıcı uçtan uca testi değildir. Sağlayıcı ve ağ politikası testlerinin bir kısmı kontrollü yanıtlar kullanır.

## Bu oturumdaki sınırlar

Önceki hata kontrolünde tam paket denendi: 11 gerçek loopback bağlantı testi işletim sisteminin `WinError 10013` erişim kısıtına takıldı. Bunlar geçmiş kabul edilmez. Aynı HTTP sözleşmeleri, bağlantı açmayan 13 bellek testiyle ayrıca kontrol edildi; bu kontrol gerçek socket/tarayıcı testinin yerine geçtiği iddiası taşımaz.

Gerçek HIBP abonelik anahtarı verilmedi; canlı HIBP hesap sorgusu yapılmadı. Resmi API belgeleri kontrol edildi, sağlayıcı yanıtları ve tüm durumlar kontrollü test verisiyle doğrulandı. ipwho.is için canlı sorgu ve güncel tarayıcı/Windows başlatıcısı bu oturumda doğrulanamadı. Önceki çalışmada Windows başlatıcısı, CIDR, canlı Google DNS ve vaka JSON/HTML aktarımı gerçek ortamda doğrulanmıştı; bu geçmiş kayıt yeni düzeltmelerin canlı doğrulaması sayılmaz.

Pillow/pypdf/phonenumbers/mutagen isteğe bağlı adaptörleri gerçek dosya/numara örnekleriyle bu ortamda doğrulanmadı. Sağlayıcı kotaları ve erişim politikaları geçerlidir. Entegrasyon gerekli kartları uygulanmış/test edilmiş araç sayılmaz. Güncel kapsam: 111 kart; 45 çalışıyor, 36 kısmi, 30 entegrasyon gerekli. Son eklenen #106–110 araçları yerel ve anahtarsızdır. Yapımcı TarikPro43391, sürüm v1.0.0 olarak doğrulandı.

## Yeniden çalıştırma

Ağ bağlantısı gerektirmeyen Python grupları:

```text
python -m unittest discover -s tests -p test_tools.py -v
python -m unittest discover -s tests -p test_ip_lookup.py -v
python -m unittest discover -s tests -p test_http_memory.py -v
python -m unittest discover -s tests -p test_extra_tools.py -v
python -m unittest discover -s tests -p test_hibp.py -v
python -m unittest discover -s tests -p test_oathnet.py -v
```

Node 18+ varsa arayüz kontrolleri (uygulamayı başlatmak için Node gerekmez):

```text
node tests/test_frontend.mjs
```

Gerçek loopback bağlantılarına izin verilen ortamda bütün Python testleri:

```text
python -m unittest discover -s tests -v
```

## HIBP kurulum durumu

Adaptör hazırdır; gerçek e-posta sorgularını çalıştırmak için Ayarlar → Have I Been Pwned bölümüne geçerli HIBP abonelik anahtarı girilmelidir. Anahtar sunucu belleğinde tutulur. IP sorgusuna anahtar gereksinimi eklenmedi. Başlangıçta #50, anahtar yoksa entegrasyon gerekli olarak görünür.

## OathNet doğrulama sınırı

Resmi kimlik doğrulama ve breach-search rehberi kontrol edildi. Gerçek API anahtarı verilmedi; canlı OathNet sorgusu yapılmadı. Testlerde kontrollü sağlayıcı yanıtları kullanıldı. Doğrudan endpoint referansı erişilemediği için sözleşme resmi rehberdeki V2 filtre/yanıt örneğine göre uygulandı; plan/şema değişiklikleri gerçek kullanımda hata olarak gösterilir. Tarayıcı uçtan uca doğrulaması bu oturumda yapılmadı.

## Ek hata kontrolü · sürüm değişmeden

- Analiz sürerken vaka değiştirme/temizleme engellendi; dosya okunurken analiz başlarsa içe aktarma ikinci kez denetlenir. Sonuç yanlış vakaya eklenmez.
- Anahtar güncellemeleri tek işlem kilidiyle sıraya alınmadan çakışmaya kapatıldı. İşlem boyunca bütün anahtar düğmeleri devre dışıdır; başarı/hata sonrasında açılır. Sunucu ayarı kaydedip katalog yenilemesi başarısız olursa bu kısmi sonuç açıkça belirtilir; istek reddinde girdi korunur.
- HTTP Content-Length ile alınan bayt sayısı eşleşmiyorsa yanıt reddedilir. Yarım kalan 404 cevabı da temiz/boş sonuç sayılmaz.
- İlk doğrulanmış IP erişilemiyorsa en fazla üç ek doğrulanmış IP denenir. DNS tekrar çözülmez, bütün adresler genel IP denetiminden geçmiştir. Toplam zaman bütçesi korunur. TLS sertifika hatası başka IP denenerek aşılmaz.
- Web URL'lerinde port 0 ve boş kullanıcı bilgisi içeren URL biçimi reddedilir.
- Aktif TCP testi yetki alanı yalnızca gerçek JSON `true` değeriyle kabul edilir; `"false"`, `"true"` veya `1` onay sayılmaz.

Bu senaryolar kontrollü ağ yanıtları ve arayüz VM testleriyle yeniden doğrulandı. Gerçek HIBP/OathNet anahtarı kullanılmadı; canlı API ve gerçek tarayıcı doğrulaması bu oturumda yapılmadı. Önceki canlı bağlantı kısıtları geçerlidir. v1.0.0 ve TarikPro43391 korunmuştur.
