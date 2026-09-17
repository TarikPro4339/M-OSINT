```markdown
# M-OSINT v0.0.3 (Alpha)

> ⚠️ Bu araç **sadece eğitim amaçlıdır.** İzinsiz sistemlerde kullanmak yasaktır.

```text
  ███╗   ███╗      ██████╗ ███████╗██╗███╗   ██╗████████╗
  ████╗ ████║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
  ██╔████╔██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║
  ██║╚██╔╝██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║
  ██║ ╚═╝ ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═╝     ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝

```

**👤 Yapımcı:** [TarikPro43391](https://github.com/TarikPro4339)

---

## ⚡ Özellikler

| Modül | Açıklama | Kaynak |
| --- | --- | --- |
| 🔓 Breach & Leak | Email sızıntı kontrolü | LeakCheck + HudsonRock + HIBP |
| 🦠 Infostealer | Zararlı yazılım tespiti | HudsonRock Cavalier |
| 🔑 Şifre Kontrolü | k-Anonymity ile sızıntı tarama | HIBP PwnedPasswords |
| 🌐 IP Sorgu | Konum, ISP, ASN, Blacklist | ipinfo.io |
| 🗺 Harita | IP konumunun harita üzerinde gösterimi | Leaflet + OpenStreetMap |
| 🖥 DNS Sorgu | A, MX, NS, TXT, WHOIS | dnspython |
| 🔌 Port Tarama | TCP + Banner Grabbing | Native Python |
| 📧 Email Analiz | MX, Gravatar, format kontrolü | Native |
| 📱 Telefon Sorgu | Telefon numarası konum ve operatör bilgisi | Public API |
| 🔌 MAC Sorgu | MAC adresinden üretici (OUI) tespiti ve bit analizi | Public API / Native |
| 🧩 Encode/Decode | Base64, URL, Hex, ROT13 (Tamamen çevrimdışı) | Native Python |
| 📡 Gerçek Zamanlı | WebSocket ile canlı tarama | Flask-SocketIO |

---

## 📝 Sürüm Notları

### v0.0.3 (Alpha) - *Mevcut Sürüm*

**✨ Yeni**

* 🔌 **MAC Vendor Sorgusu:** MAC adresinden üretici (OUI) tespiti ile local-admin/multicast bit analizi eklendi.
* 🧩 **Encode/Decode Aracı:** API gerektirmeyen, tamamen offline çalışan Base64, URL, Hex ve ROT13 dönüştürücü eklendi.
* 📡 **Canlı Tarama Güncellemesi:** WebSocket modülüne `mac` tarama tipi desteği eklendi.
* ⚙️ **Altyapı & Arayüz:** Yeni `/api/mac` ve `/api/encode` endpoint'leri eklendi. Navigasyon sekmeleri, sayfa bölümleri ve versiyon etiketleri güncellendi.

### v0.0.2 (Alpha)

**✨ Yeni**

* 📱 Telefon Sorgu modülü eklendi
* 🗺 Harita modülü eklendi (IP konumu harita üzerinde)
* 🐛 Arayüz iyileştirmeleri ve küçük hata düzeltmeleri yapıldı

---

## 🚀 Kurulum

### 1. Repoyu İndir

```bash
git clone [https://github.com/TarikPro4339/M-OSINT.git](https://github.com/TarikPro4339/M-OSINT.git)
cd M-OSINT

```

### 2. Bağımlılıkları Yükle

```bash
pip install flask flask-socketio requests dnspython python-whois eventlet

```

### 3. Çalıştır

#### Windows (Kolay Yol)

```
M-OSINT.bat dosyasına çift tıkla

```

#### Manuel

```bash
python mosint_v003.py

```

### 4. Paneli Aç

```
[http://127.0.0.1:5000](http://127.0.0.1:5000)

```

---

## 📁 Dosya Yapısı

```text
M-OSINT/
├── mosint.py     ← Tüm uygulama (tek dosya)
└── start.bat     ← Windows başlatıcı (otomatik kurulum)

```

---

## 🔧 Opsiyonel API Ayarları

```python
# mosint.py içinde üst kısım
HIBP_API_KEY = ""    # haveibeenpwned.com
IPINFO_TOKEN = ""    # ipinfo.io

```

> Boş bırakılsa da çalışır.

---

## 🛠 Kullanılan Teknolojiler

```text
Backend   → Python 3, Flask, Flask-SocketIO
Frontend  → HTML, CSS, JavaScript, Leaflet
Servisler → LeakCheck.io, HudsonRock, HIBP, ipinfo.io, MAC Vendor APIs

```

---

## ⚖️ Yasal Uyarı

```text
Bu araç yalnızca eğitim ve araştırma amaçlıdır.

✅ İzin verilen sistemlerde kullanın
✅ Kendi verilerinizi test edin
❌ Başkalarına izinsiz uygulamak → TCK 135-136
❌ Ticari amaçla kullanmayın

```

> Geliştirici hiçbir kötüye kullanımdan sorumlu değildir.

---

## 📄 Lisans

MIT License

---
