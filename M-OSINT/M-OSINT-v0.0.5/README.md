# M-OSINT v0.0.5 (Alpha)

Yerel olarak çalışan OSINT paneli. Başlatmak için Windows'ta `M-OSINT.bat`
dosyasını çalıştırın; panel varsayılan olarak `http://127.0.0.1:5000` adresinde açılır.

## v0.0.5 yenilikleri

1. **E-posta güvenliği** — alan adı için MX, SPF, DMARC ve NS kayıtlarını ve 100 üzerinden koruma puanını gösterir.
2. **Web ayak izi** — `robots.txt` içindeki yol ve sitemap işaretlerini toplar.
3. **security.txt denetimi** — RFC 9116 güvenlik iletişim dosyasını iki standart konumda kontrol eder.
4. **IOC çıkarıcı** — yapıştırılan metindeki URL, e-posta, IP, alan adı ve hash değerlerini ağ isteği yapmadan ayıklar.
5. **Şifre gücü analizi** — uzunluk, karakter çeşitliliği ve tahmini entropiye göre yerel puanlama yapar; sonuç kaydedilmez.

## Düzeltmeler

- Boş ya da JSON olmayan API istekleri artık 500 hatası vermeden güvenli varsayılanlarla işlenir.
- Telefon numaralarında karakter/uzunluk doğrulaması eklendi.
- Özel port aralığı 1–65535 ve en fazla 1.024 port ile sınırlandı.
- WebSocket CORS erişimi yalnızca yerel panel adresine daraltıldı.
- Sabit uygulama anahtarı yerine `MOSINT_SECRET_KEY` ortam değişkeni desteklendi.
- Başlatıcı Python 3.14'ü desteklenen sürüm aralığına ekledi ve yeni kaynak dosyayı başlatır.

Bu araç yalnızca yetkili, yasal ve eğitim amaçlı araştırmalarda kullanılmalıdır.
