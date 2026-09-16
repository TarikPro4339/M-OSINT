# M-OSINT v0.0.1 (Alpha)

> ⚠️ Bu araç **sadece eğitim amaçlıdır.** İzinsiz sistemlerde kullanmak yasaktır.

```
  ███╗   ███╗      ██████╗ ███████╗██╗███╗   ██╗████████╗
  ████╗ ████║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
  ██╔████╔██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║
  ██║╚██╔╝██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║
  ██║ ╚═╝ ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═╝     ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
```

---

## ⚡ Özellikler

| Modül | Açıklama | Kaynak |
|-------|----------|--------|
| 🔓 Breach & Leak | Email sızıntı kontrolü | LeakCheck + HudsonRock + HIBP |
| 🦠 Infostealer | Zararlı yazılım tespiti | HudsonRock Cavalier |
| 🔑 Şifre Kontrolü | k-Anonymity ile sızıntı tarama | HIBP PwnedPasswords |
| 🌐 IP Sorgu | Konum, ISP, ASN, Blacklist | ipinfo.io |
| 🖥 DNS Sorgu | A, MX, NS, TXT, WHOIS | dnspython |
| 🔌 Port Tarama | TCP + Banner Grabbing | Native Python |
| 📧 Email Analiz | MX, Gravatar, format kontrolü | Native |
| 📡 Gerçek Zamanlı | WebSocket ile canlı tarama | Flask-SocketIO |

---

## 🚀 Kurulum

### 1. Repoyu İndir

```bash
git clone https://github.com/TarikPro4339/M-OSINT.git
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
Frontend  → HTML, CSS, JavaScript
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
  <sub>M-OSINT v0.0.1 Alpha — Eğitim Amaçlı</sub>
</div>
