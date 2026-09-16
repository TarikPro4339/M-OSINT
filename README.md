# M-OSINT v0.0.2 (Alpha)

> ⚠️ Bu araç **sadece eğitim amaçlıdır.** İzinsiz sistemlerde kullanmak yasaktır.

```
  ███╗   ███╗      ██████╗ ███████╗██╗███╗   ██╗████████╗
  ████╗ ████║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
  ██╔████╔██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║
  ██║╚██╔╝██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║
  ██║ ╚═╝ ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═╝     ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
```

**👤 Yapımcı:** [TarikPro43391](https://github.com/TarikPro43391)

---

## ⚡ Özellikler

| Modül | Açıklama | Kaynak |
|-------|----------|--------|
| 🔓 Breach & Leak | Email sızıntı kontrolü | LeakCheck + HudsonRock + HIBP |
| 🦠 Infostealer | Zararlı yazılım tespiti | HudsonRock Cavalier |
| 🔑 Şifre Kontrolü | k-Anonymity ile sızıntı tarama | HIBP PwnedPasswords |
| 🌐 IP Sorgu | Konum, ISP, ASN, Blacklist | ipinfo.io |
| 🗺 Harita | IP konumunun harita üzerinde gösterimi | Leaflet + OpenStreetMap |
| 🖥 DNS Sorgu | A, MX, NS, TXT, WHOIS | dnspython |
| 🔌 Port Tarama | TCP + Banner Grabbing | Native Python |
| 📧 Email Analiz | MX, Gravatar, format kontrolü | Native |
| 📱 Telefon Sorgu | Telefon numarası konum ve operatör bilgisi | Public API |
| 📡 Gerçek Zamanlı | WebSocket ile canlı tarama | Flask-SocketIO |

---

## 📝 Sürüm Notları — v0.0.2

**✨ Yeni**
- 📱 Telefon Sorgu modülü eklendi
- 🗺 Harita modülü eklendi (IP konumu harita üzerinde)

**🐛 Düzeltildi**
- Birkaç küçük hata düzeltildi
- Arayüz ve kararlılık iyileştirmeleri yapıldı

---

## 🚀 Kurulum

### 1. Repoyu İndir

```bash
git clone https://github.com/TarikPro43391/M-OSINT.git
```

```bash
cd M-OSINT
```

### 2. Bağımlılıkları Yükle

```bash
pip install flask flask-socketio requests dnspython python-whois eventlet
```

### 3. Çalıştır

#### Windows (Kolay Yol)
```
start.bat dosyasına çift tıkla
```

#### Manuel
```bash
python mosint.py
```

### 4. Paneli Aç

```
http://127.0.0.1:5000
```

---

## 📁 Dosya Yapısı

```
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

```
Backend   → Python 3, Flask, Flask-SocketIO
Frontend  → HTML, CSS, JavaScript, Leaflet
Servisler → LeakCheck.io, HudsonRock, HIBP, ipinfo.io
```

---

## ⚖️ Yasal Uyarı

```
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

<div align="center">
  <sub>M-OSINT v0.0.2 Alpha — Eğitim Amaçlı — Geliştirici: TarikPro43391</sub>
</div>
