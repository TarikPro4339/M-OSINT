# Güvenlik modeli

## Sınır

Tek kullanıcı, yerel makine, 127.0.0.1. Flask/eventlet, debug reloader, WebSocket CORS veya dış CDN bağımlılığı yok. Python standart kitaplığındaki HTTP sunucusu özel, sınırlı handler ile kullanılır; internet yayını için uygun değildir. Uygulamada hesap/parola oturumu yoktur; yerel API anahtarı ve origin denetimi başka sitelerden istek sahteciliğini azaltır, yerel süreçlere karşı kimlik doğrulaması sağlamaz.

## Ağ

- Varsayılan ağ kapalıdır; her sorguda `network_consent: true` gerekir.
- TCP testleri ayrıca `authorized: true` ister. Tek genel hedef, en fazla 16 port, dört çalışan; veri gönderen servis yoklaması ve UDP yok.
- HTTP/HTTPS, yalnızca 80/443. Kullanıcı bilgisi, boşluk/denetim karakterleri ve backslash içeren URL reddedilir.
- DNS sonuçlarının **tamamı** genel olmalı; karışık genel/özel yanıt reddedilir.
- Bağlantı doğrulanmış adrese yapılır; TLS SNI/sertifika özgün alan adıyla denetlenir. Yeniden DNS çözerek başka IP'ye bağlanma yapılmaz.
- IPv4-mapped IPv6, 6to4 ve Teredo web/TCP hedeflerinde engellenir. İç ağ ve bulut metadata link-local adresleri engellenir.
- Her yönlendirme tekrar doğrulanır. HTTPS→HTTP reddedilir. Authorization başlığı yönlendirmeye taşınmaz.
- Dört saniye DNS/socket aşımı, HTTP toplam 20 saniye, dört yönlendirme ve 1 MiB yanıt sınırı. OS DNS çözümünün süresi işletim sistemine de bağlıdır; arka planda en fazla dört çözüm sürer.
- HTTP sıkıştırması istenmez; sıkıştırılmış yanıt reddedilir. Çerez kavanozu yoktur. Ortam proxy değişkenleri kullanılmaz.
- Sunucu 12 bağlantı, 2 iş ve dakikada 60 POST ile sınırlıdır. Kotalar tüm yerel sekmeler arasında ortaktır.

## Girdi ve çıktı

Shell, eval, komut satırı üretimi, arşiv çıkartma, betik çalıştırma yok. Statik dosyalar yalnızca sabit izin listesinden sunulur. XSS için DOM textContent/createElement kullanılır; kullanıcı/sağlayıcı HTML'i çalıştırılmaz. Bağlantılar yalnızca http/https ve kullanıcı bilgisi olmadan açılır; noopener/noreferrer uygulanır. Dışa aktarılan HTML kaçışlanır ve betik çalıştırmayan CSP taşır; CSV hücreleri formül enjeksiyonuna karşı zırhlanır.

Dosyalar base64 JSON ile yalnızca yerel Python sürecine gelir, diske yazılmaz veya üçüncü tarafa gönderilmez. Bu işlem sırasında geçici RAM kopyaları oluşur; kriptografik bellek silme garantisi yoktur. ZIP boyut/oran ve XML DTD/entity denetimleri vardır. Optional parser paketlerini güncel tutun. İş parçacığı modeli kötü niyetli bir parser girdisinin CPU/bellek tüketimine karşı tam izolasyon sağlamaz.

## Doğruluk

Varsayılan olarak ihlal veya hesap varlığı hakkında sonuç uydurulmaz. Genel ihlal listesi kişisel ihlal kanıtı sayılmaz. 404, kota, ağ hatası ve sağlayıcı reddi “yok” olarak normalize edilmez. HTML araçları HTTP durumunu gösterir. Hesap, numara veya cüzdan biçim uygunluğu sahiplik/aktiflik doğrulaması değildir. Statik veri listeleri kısmi olarak etiketlenir.

## Anahtarlar ve vaka verisi

IPinfo, HIBP ve OathNet anahtarları yalnızca süreç belleğinde; UI'ya geri döndürülmez. Sunucu erişim/sorgu gövdelerini günlüğe yazmaz. Vaka içeriği varsayılan sekme belleğinde; localStorage yalnızca kullanıcı tercihiyle, şifresiz. Dışa aktarılan vaka ve raporların korunması kullanıcıya aittir. Python süreç belleği, swap veya tarayıcı eklentilerine karşı koruma iddiası yoktur.

Sorumlu kullanım: yalnızca yetkili hedeflerde ve kamuya açık kaynaklarda araştırma. Sunucu genel-IP sınırını yerel ağı taramak için kaldırmayın; ayrı, kapsamı onaylanmış test altyapısı kullanın.

## HIBP adaptörü

Tek adres sorgusu resmi HTTPS breachedaccount uç noktasına gider. Tam adres gönderimi her çalıştırmada ağ onayı gerektirir. Anahtar HTTP başlığındadır; yönlendirme takibi kapalıdır, anahtar/yanıt gövdesi hata mesajına kopyalanmaz. 404 yalnızca HIBP kapsamındaki kayıt yokluğudur; diğer hatalar temiz sonuç değildir. Doğrulanmamış, hassas ve emekli ihlaller kapsam dışıdır. HTML açıklamalar ve sızıntı içerikleri alınmaz. E-posta ve sonuçlar yerel oturum vakasına girebilir; HIBP anahtarı dahil edilmez. Ayrı sağlayıcı anahtarları bağımsız güncellenir.

## OathNet adaptörü

Tek ASCII e-posta, açık ağ onayıyla resmi HTTPS V2 breach/search servisine gönderilir. Anahtar yalnızca x-api-key başlığındadır; yönlendirme takibi kapalıdır. İlk sayfa ile sınırlıdır, 500 kayıt/1 MiB taşıma sınırında çalışır. Ham sağlayıcı yanıtı RAM’de işlenebilir; yalnızca eşleşen adresin dbname alanları ve sayılar sonuç nesnesine taşınır. Parola, hash, token, cursor ve diğer satır alanları vaka/rapora dahil edilmez. Başka adrese ait satır dönerse sonuç reddedilir. Kota veya şema hatası kayıt yok sonucu değildir. Kriptografik RAM silme garantisi yoktur.

## Bağlantı ve oturum tutarlılığı

Aynı DNS çözümünden genel olduğu doğrulanan en fazla dört IP, bağlantı kurulamadığında sırayla denenebilir. Yeni DNS çözümü veya özel IP alternatifi kullanılmaz. Sertifika doğrulama hatası kesin hatadır. Content-Length tutarsızlığı sonucu bilinmiyor olarak reddedilir. Aktif TCP yetki alanı gerçek boolean true olmalıdır. Arayüz, analiz sürerken vaka değiştirme/temizlemeyi ve anahtar ayarlarında eşzamanlı yazmayı engeller.
