# M-OSINT v0.0.8

Yerelde çalışan, tek dosyalık Flask tabanlı OSINT ve savunma analizi paneli. WebSocket ile canlı tarama çıktısı verir ve neon temalı bir arayüze sahiptir.

> **Yapımcı:** tarikpro43391
> Bu araç yalnızca yetkili, yasal ve eğitim amaçlı araştırmalarda kullanılmalıdır. İzniniz olmayan sistemleri taramayın.

## Hızlı başlangıç (Windows)

1. Klasörü zip'ten çıkarın.
2. `M-OSINT.bat` dosyasını çalıştırın.
3. İlk çalıştırmada başlatıcı Python'u kontrol eder, `.venv` ortamını ve bağımlılıkları kurar.
4. Panel `http://127.0.0.1:5000` adresinde açılır.
5. Durdurmak için terminalde `Ctrl+C` tuşlarına basın.

### Elle çalıştırma (Windows / Linux / macOS)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python mosint_v008.py
```

**Gereksinimler:** Python 3.9+ ve `requirements.txt` içindeki paketler (flask, flask-socketio, requests, dnspython, python-whois, eventlet).

## Özellikler

| Kategori | Modüller |
|---|---|
| Sızıntı / kimlik | E-posta sızıntı taraması (LeakCheck, HudsonRock, HIBP), şifre pwned kontrolü, e-posta kontrolü |
| Kişi / hesap | Telefon analizi (TR operatörleri), kullanıcı adı arama (46 platform) |
| Alan adı / ağ | DNS, WHOIS, subdomain taraması, CertIntel (crt.sh), IP bilgisi + kara liste, port tarayıcı, MAC üretici |
| Web güvenliği | URL analizi (güvenlik skoru), SSL/TLS analizi |
| Yardımcı | Hash analizi / sözlük çözücü, Base64 / URL / Hex / ROT13 dönüştürücü |
| Canlı | WebSocket ile gerçek zamanlı tarama terminali |
| Araç kutusu | 15 savunma odaklı araç (aşağıda) |

## Araç kutusu

### v0.0.8 — yeni

1. **HTTP güvenlik başlıkları denetimi** — HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy ve COOP başlıklarını puanlar ve A–F not verir. `Server` / `X-Powered-By` sürüm sızıntılarını ve çerezlerdeki Secure / HttpOnly / SameSite eksiklerini listeler.
2. **Yönlendirme zinciri izleyici** — Bağlantının her yönlendirme adımını gövde indirmeden izler (en fazla 10). Döngü, HTTPS→HTTP düşürme, uzun zincir ve çok alan adından geçen zincirleri işaretler.
3. **JWT inceleyici** — Token'ı yerelde çözer; imza **doğrulanmaz**. `alg=none`, süresi dolmuş veya `exp`'siz token, `jku` / `x5u` / `kid` başlıkları ve payload'daki hassas alanları işaretler.
4. **E-posta başlığı analizi** — Ham başlıklardan Received zincirini, SPF / DKIM / DMARC sonuçlarını ve From / Return-Path / Reply-To uyuşmazlıklarını çıkarır, phishing risk puanı üretir. Ağ isteği yapılmaz.
5. **CIDR / alt ağ hesaplayıcı** — Ağ, yayın, maske, wildcard, kullanılabilir host aralığı ve ikiye bölme önerisi. `10.0.0.5 in 10.0.0.0/24` biçiminde üyelik kontrolü yapar (IPv4 + IPv6).

### v0.0.7

- Defanged IOC normalleştirici (`hxxps://ornek[.]com`)
- IOC CSV dışa aktarma
- DNS sertleştirme görünürlüğü (CAA, DNSKEY, DS)
- Alan adı kayıt özeti (WHOIS: kuruluş, yaş, tarihler, ad sunucuları)
- E-posta politikası denetimi (SPF sonlandırıcısı, DMARC politikası)
- IOC çıkarıcı, security.txt denetimi, web ayak izi (robots.txt / sitemap), SPF/DMARC/MX özeti
- Yerel şifre gücü analizi

## v0.0.8 değişiklik günlüğü

- **Eklendi:** HTTP başlık denetimi, yönlendirme izleyici, JWT inceleyici, e-posta başlığı analizi, CIDR hesaplayıcı.
- **Güvenlik:** HTTP tabanlı yeni araçlar yalnızca genel (public) IP'lere çözülen hedeflere istek atar; bu kontrol her yönlendirme adımında tekrarlanır (iç ağa SSRF engeli). Yerel bir siteyi test etmek isterseniz `mosint_v008.py` içindeki `_is_public_host` fonksiyonunu geçici olarak değiştirin.
- **Arayüz:** JWT, e-posta başlığı ve IOC araçlarında çok satırlı metin alanı kullanılır; araç menüsü sürüme göre gruplandı.
- **Dosya adı:** `mosint_v007.py` → `mosint_v008.py`.

## Yerel API

Tüm uç noktalar `POST` kabul eder, JSON döner ve istek boyutu 64 KB ile sınırlıdır.

| Uç nokta | Gövde alanı |
|---|---|
| `/api/http-headers` | `target` |
| `/api/redirect-trace` | `target` |
| `/api/jwt` | `token` |
| `/api/email-headers` | `text` |
| `/api/cidr` | `text` |
| `/api/email-auth`, `/api/email-policy`, `/api/dns-hardening` | `domain` |
| `/api/footprint`, `/api/security-txt`, `/api/domain-registration` | `target` |
| `/api/ioc-extract`, `/api/ioc-normalize`, `/api/ioc-csv` | `text` |
| `/api/password-strength` | `password` |

Örnek:

```bash
curl -s -X POST http://127.0.0.1:5000/api/cidr \
  -H "Content-Type: application/json" \
  -d '{"text":"192.168.1.10/24"}'
```

## Güvenlik notları

- Sunucu varsayılan olarak yalnızca `127.0.0.1` üzerinde dinler; internete açmayın.
- `MOSINT_SECRET_KEY` ortam değişkeni verilmezse her başlangıçta rastgele bir oturum anahtarı üretilir.
- Şifre, JWT ve e-posta başlıkları kaydedilmez; yalnızca yerel servis tarafından işlenir.
- Bazı modüller (HIBP, IPinfo vb.) API anahtarı gerektirir; anahtarları `mosint_v008.py` başındaki yapılandırma bölümüne girin.
- Yapılan taramalardan ve sonuçların kullanımından kullanıcı sorumludur.

## Dosyalar

```
M-OSINT-v0.0.8/
├── mosint_v008.py     # uygulama (Flask + SocketIO, arayüz dahil)
├── M-OSINT.bat        # Windows başlatıcı (venv + bağımlılık + tarayıcı)
├── requirements.txt
└── README.md
```
