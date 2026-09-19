# M-OSINT v0.0.7

Yerel çalışan OSINT ve savunma analizi paneli. Windows'ta `M-OSINT.bat` dosyasını çalıştırın; panel varsayılan olarak `http://127.0.0.1:5000` adresinde açılır.

## v0.0.7 yenilikleri

1. **Defanged IOC normalleştirici** — `hxxps://ornek[.]com` gibi güvenli paylaşılan göstergeleri yerelde standart biçime getirir ve IOC'leri ayıklar; ağ isteği yapmaz.
2. **IOC CSV dışa aktarma** — IOC veya defanged IOC metnini yerelde normalleştirip tür/değer biçiminde CSV çıktısına dönüştürür.
3. **DNS sertleştirme görünürlüğü** — CAA, DNSKEY ve DS kayıtlarını inceler; bu sinyaller DNSSEC doğrulaması olarak sunulmaz.
4. **Alan adı kayıt özeti** — WHOIS verisinden kayıt kuruluşu, alan adı yaşı, tarihler ve ad sunucularını bir arada gösterir.
5. **E-posta politikası denetimi** — SPF sonlandırıcısını ve DMARC uygulama politikasını sahteciliğe karşı koruma açısından yorumlar.
6. **Daha güvenli oturum anahtarı** — `MOSINT_SECRET_KEY` verilmedikçe uygulama her başlangıçta rastgele bir anahtar üretir.
7. **İstek boyutu sınırı** — yerel API istekleri 64 KB ile sınırlıdır.

## Çalıştırma

1. `M-OSINT.bat` dosyasını açın.
2. İlk çalıştırmada başlatıcı izole Python ortamını ve bağımlılıkları kurar.
3. Tarayıcıdaki yerel paneli kullanın. Sunucuyu durdurmak için terminalde `Ctrl+C` tuşlarına basın.

Bu araç yalnızca yetkili, yasal ve eğitim amaçlı araştırmalarda kullanılmalıdır.
