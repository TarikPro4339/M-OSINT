# Uygulanan kaynaklar ve adaptör belgeleri

Kontrol tarihi: 4 Kasım 2026. Sağlayıcı değişiklikleri/kotaları uygulamadan bağımsızdır. Canlı ağ isteği yalnızca açık izinle yapılır.

- Have I Been Pwned resmi e-posta API: https://haveibeenpwned.com/API/v3
- HIBP abonelik anahtarı: https://haveibeenpwned.com/API/Key
- Google Public DNS JSON: https://developers.google.com/speed/public-dns/docs/doh/json
- Anahtarsız IP/ASN (varsayılan): https://ipwhois.io/documentation
- IPinfo Lite (isteğe bağlı alternatif): https://ipinfo.io/developers/lite-api
- GitHub genel kullanıcı REST: https://docs.github.com/en/rest/users/users
- GitHub kullanıcı depoları: https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user
- Discord Get Invite: https://docs.discord.com/developers/resources/invite#get-invite
- RDAP protokolü: https://www.rfc-editor.org/rfc/rfc9082
- RDAP bootstrap hizmeti: https://about.rdap.org/
- Sertifika arama: https://crt.sh/
- ipify: https://www.ipify.org/
- Pillow EXIF: https://pillow.readthedocs.io/en/stable/reference/Image.html
- pypdf: https://pypdf.readthedocs.io/
- phonenumbers: https://github.com/daviddrysdale/python-phonenumbers
- Mutagen: https://mutagen.readthedocs.io/
- Yerel Python HTTP güvenlik sınırları: https://docs.python.org/3/library/http.server.html#security-considerations

Profil URL şablonları ve arama/harita/radar bağlantıları yalnızca gezinme kolaylığıdır. Platform URL'leri değişebilir; gerçek hesap varlığı veya kimlik kanıtı olarak değerlendirilmez. Telegram HTML önizleme ve crt.sh JSON erişimi sağlayıcının o günkü sunumuna bağlıdır.

## Sağlayıcı gerektiren özellik nasıl tamamlanır?

1. İlgili kartın `mosint/catalog.py` kapsam notunu okuyun; yetki/mahremiyet ve sağlayıcı koşullarını belirleyin.
2. Anahtarları kod/JSON vaka dosyasına yazmayın; süreç belleğinde sunucu tarafında tutun.
3. Sabit sağlayıcı URL'si ve doğrulanmış şema kullanın; ağ hedeflerini `network.fetch` taşıyıcısından geçirin.
4. Kota/401/403/404/ağ hatasını “bulunamadı” sonucuna çevirmeyin. Kimlik/sahiplik konusunda desteklenmeyen çıkarım yapmayın.
5. Gerçek adaptör ve testleri ekledikten sonra katalogdaki durumu ve kapsam tablosunu güncelleyin. Yalnızca kartı açmak entegrasyon değildir.

## OathNet resmi kaynakları

- API kimlik doğrulama: https://docs.oathnet.org/introduction/authentication
- Breach arama sözleşmesi ve yanıt örneği: https://docs.oathnet.org/guides/breach-search
- API yanıt aileleri: https://docs.oathnet.org/api-reference/overview

Adaptör yalnızca V2 breach/search tek e-posta filtresini kullanır; bütün OathNet servisleri veya tam sayfalama uygulanmış değildir.
