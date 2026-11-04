# v0.0.8 → 1.0

İncelenen özgün ZIP: `M-OSINT-main.zip`.

SHA-256: `7bc42b71cf616a45842cb7be32b9cae3a33ade6ce8a4fefbc72d0821d132286e`.

ZIP'te kök README/LICENSE ile `M-OSINT-v0.0.8/{M-OSINT.bat,README.md,mosint_v008.py,requirements.txt}` vardı. 201.570 baytlık tek Python dosyası Flask, SocketIO ve eventlet ile arayüz ve araçları birlikte içeriyordu.

## Korunanlar

M-OSINT adı, yapımcı atfı ve özgün MIT LICENSE. Verilen ASCII dosyası atıflarıyla birlikte statik intro varlığına alındı. 105 özellik listesi ve sırası korunarak katalog oluşturuldu. Ağ/DNS/TLS, JWT, başlık, CIDR, IOC ve kodlama araçlarının amaçları yeni, bağımsız işleyicilerde sürdürüldü.

## Yeniden düzenlenenler

`mosint_v008.py` içindeki uygulama, doğrudan içe aktarılmadan modüler çekirdekle değiştirildi. Bu sürümün launcher'ı eski programı başlatmaz. Flask/eventlet/SocketIO zorunlulukları kaldırıldı; çekirdek Python standart kitaplığıyla çalışır. UI statik ayrı dosyalardır; sonuçlar POST cevabıyla gelir. Sahte canlı tarama satırları veya WebSocket tarama akışı gösterilmez. İşlem sırasında gerçek bekleme durumu ve tamamlanınca gerçek sonuç vardır.

Özgün `breach_hibp` genel ihlal listesini alıp e-posta domainiyle eşleştiriyordu. Bu, ilgili kişisel hesabın ihlal edildiğini kanıtlamaz. #50 artık resmi HIBP hesap sorgusu adaptörünü kullanır; abonelik anahtarı gerekir. Genel liste kişisel ihlal kanıtı sayılmaz.

Sınırsız veya sahipliği belirsiz otomasyon yerine tek hedef TCP sınırları, açık ağ/yetki onayı, her yönlendirmede IP sabitleme ve Origin/Host/istek anahtarı koruması eklendi. Eski API yolları uyumlu tutulmadı; `/api/run` ve numaralı katalog kullanılır. Kaynak dosyasına anahtar yazma yerine yalnızca süreç belleğinde IPinfo yapılandırması vardır.

Eski kişisel ihlal/stealer sorguları, parola tarama/çözme ve otomatik hesap eşleştirmeleri yeni arayüze aktarılmadı. Bu, eski sürümün bütün araçlarıyla API uyumlu bir sürüm değildir; verilen 105 isteği açık kapsamla ele alan yerel çalışma alanıdır.

## Anahtarsız IP sorgusu

#1 ve #2 artık açılışta kullanılabilir. Varsayılan HTTPS sağlayıcısı ipwho.is; API anahtarı veya hesap gerekmez. IPinfo Lite yalnızca kullanıcı bir anahtar girerek alternatifi seçerse kullanılır. Sağlayıcının success:false yanıtı ve eksik/uyumsuz IP veya ASN yanıtı başarı olarak gösterilmez. Ağ izni ve genel IP kontrolü korunmuştur.

## Sürüm tercihi ve hata düzeltmeleri

Kullanıcının talebiyle sürüm v1.0.0 olarak sabitlendi. Kullanıcı açıkça istemedikçe sürüm değiştirilmez. IPv6 düşük sayısal adreslerde adres ailesi, büyük vaka önizlemelerinin geri açılması, dosya okunurken çift gönderim ve geçersiz yerel oturum başlığının hata cevabı düzeltildi. Arayüz/rapor sürümü sunucunun sürüm bilgisinden alınır.

## Beş ek yerel araç

#106–110 eklendi; özgün 105 isteğin numarası korunur. Toplam 110 kart, temiz kurulumda 45 çalışan / 36 kısmi / 29 entegrasyon gerekli. Sürüm 1.0.0 olarak kaldı; yapımcı yazımı TarikPro43391 olarak eşitlendi.

## Resmi HIBP e-posta sorgusu

#50 gerçek breachedaccount adaptörüyle bağlandı. API anahtarı bellek ayarından girilir; her adres için ağ onayı gerekir. 404/kota/yetki hatası ayrımı, anahtarların bağımsız güncellenmesi ve HIBP kaynak atfı eklendi. Sürüm 1.0.0 ve yapımcı TarikPro43391 korundu.

## OathNet bağlantısı

#111 OathNet e-posta kaynak/sayı özeti eklendi; katalog 111 kart oldu. API anahtarları bağımsız bellek ayarlarıdır. HIBP ve anahtarsız IP sorgusu korunur. Sürüm 1.0.0; yapımcı TarikPro43391.
