# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         M-OSINT Framework                            ║
# ║                       v0.0.5                                         ║
# ║                   Yapımcı: tarikpro43391                             ║
# ╚══════════════════════════════════════════════════════════════════════╝

# NOT: eventlet monkey-patch mutlaka tum diger importlardan ONCE calismali.
# Yoksa socket/ssl/whois gibi bloklayan cagrilar, tek threadli eventlet
# WSGI sunucusunun tamamini kilitler (bir tarama surerken site "donar",
# WebSocket baglantilari kopar).
import eventlet
eventlet.monkey_patch()

import sys, os, time, threading, re, socket, hashlib, ssl, json, codecs, ipaddress, math
import concurrent.futures, requests, dns.resolver, whois
from urllib.parse import urlparse
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone

# ══════════════════════════════════════════
#              KONFİG
# ══════════════════════════════════════════
APP_NAME  = "M-OSINT"
VERSION   = "v0.0.5 (Alpha)"
AUTHOR    = "tarikpro43391"
HOST      = "127.0.0.1"
PORT      = 5000
DEBUG     = False
IPINFO_TOKEN = ""

# ══════════════════════════════════════════
#              ANİMASYON
# ══════════════════════════════════════════
def clear(): os.system("cls" if os.name == "nt" else "clear")
def c(t, code): return f"\033[{code}m{t}\033[0m"

BANNER = r"""
  ███╗   ███╗      ██████╗ ███████╗██╗███╗   ██╗████████╗
  ████╗ ████║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
  ██╔████╔██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║
  ██║╚██╔╝██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║
  ██║ ╚═╝ ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═╝     ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
"""

def startup_animation():
    clear()
    for line in BANNER.split("\n"):
        print(c(line, "96"))
        time.sleep(0.04)
    time.sleep(0.1)
    rows = [
        ("  ┌──────────────────────────────────────────────────────┐", "94"),
        (f"  │  Uygulama : {APP_NAME:<43}│", "96"),
        (f"  │  Versiyon : {VERSION:<43}│", "96"),
        (f"  │  Yapımcı  : {AUTHOR:<43}│", "93"),
        (f"  │  Panel    : http://{HOST}:{PORT:<36}│", "92"),
        (f"  │  Tarih    : {datetime.now().strftime('%d.%m.%Y %H:%M:%S'):<43}│", "97"),
        ("  └──────────────────────────────────────────────────────┘", "94"),
    ]
    for row, col in rows:
        print(c(row, col))
        time.sleep(0.07)
    print()
    steps = [
        ("  [►] Breach modülleri yükleniyor", "96"),
        ("  [►] IP / DNS / Port hazırlanıyor", "96"),
        ("  [►] Telefon analiz modülü       ", "96"),
        ("  [►] Kullanıcı adı tarayıcısı (46)", "95"),
        ("  [►] SSL / Hash / CertIntel      ", "95"),
        ("  [►] Flask & WebSocket başlatılıyor", "96"),
        ("  [►] Neon panel hazırlanıyor     ", "92"),
    ]
    for step, col in steps:
        sys.stdout.write(c(step, col))
        sys.stdout.flush()
        for _ in range(4):
            time.sleep(0.12)
            sys.stdout.write(c(".", "94"))
            sys.stdout.flush()
        print(c(" TAMAM", "92"))
        time.sleep(0.07)
    print()
    print(c(f"  ✔  Sistem hazır! → http://{HOST}:{PORT}", "92"))
    print()
    print(c("  " + "─" * 52, "90"))
    print(c("  [SUNUCU LOGU]", "90"))
    print(c("  " + "─" * 52, "90"))
    print()

# ══════════════════════════════════════════
#              BREACH - LEAKCHECK
# ══════════════════════════════════════════
def breach_leakcheck(email: str) -> dict:
    r = {"source": "LeakCheck.io", "found": False,
         "breach_count": 0, "breaches": [], "fields": [], "error": None}
    try:
        res = requests.get(
            f"https://leakcheck.io/api/public?check={email}",
            headers={"User-Agent": "M-OSINT/0.0.5"},
            timeout=15
        )
        if res.status_code == 200:
            d = res.json()
            if d.get("success"):
                r["found"]        = d.get("found", 0) > 0
                r["breach_count"] = d.get("found", 0)
                r["fields"]       = d.get("fields", [])
                for s in d.get("sources", []):
                    r["breaches"].append({
                        "name": s.get("name", ""),
                        "date": s.get("date", "")
                    })
        elif res.status_code == 429:
            r["error"] = "Rate limit — biraz bekleyin"
        else:
            r["error"] = f"HTTP {res.status_code}"
    except Exception as e:
        r["error"] = str(e)
    return r

# ══════════════════════════════════════════
#              BREACH - HUDSONROCK
# ══════════════════════════════════════════
def breach_hudsonrock(email: str) -> dict:
    r = {"source": "HudsonRock", "found": False,
         "stealer_count": 0, "stealers": [], "error": None}
    try:
        res = requests.get(
            f"https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email={email}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        if res.status_code == 200:
            d  = res.json()
            st = d.get("stealers", [])
            if st:
                r["found"]         = True
                r["stealer_count"] = len(st)
                for s in st[:10]:
                    r["stealers"].append({
                        "computer_name":    s.get("computer_name",    "N/A"),
                        "operating_system": s.get("operating_system", "N/A"),
                        "date_compromised": s.get("date_compromised", "N/A"),
                        "malware_path":     s.get("malware_path",     "N/A"),
                        "antiviruses":      s.get("antiviruses",      []),
                        "total_corporate":  s.get("total_corporate_services", 0),
                        "total_user":       s.get("total_user_services",      0),
                    })
        elif res.status_code == 429:
            r["error"] = "Rate limit"
        else:
            r["error"] = f"HTTP {res.status_code}"
    except Exception as e:
        r["error"] = str(e)
    return r

# ══════════════════════════════════════════
#              BREACH - HIBP
# ══════════════════════════════════════════
def breach_hibp(email: str) -> dict:
    r = {"source": "HIBP Public", "found": False,
         "breach_count": 0, "breaches": [], "total_in_db": 0, "error": None}
    try:
        res = requests.get(
            "https://haveibeenpwned.com/api/v3/breaches",
            headers={"User-Agent": "M-OSINT/0.0.3"},
            timeout=15
        )
        if res.status_code == 200:
            all_b = res.json()
            r["total_in_db"] = len(all_b)
            domain = email.split("@")[1].lower() if "@" in email else ""
            for b in all_b:
                bd = b.get("Domain", "").lower()
                if bd and domain and (bd == domain or domain in bd or bd in domain):
                    r["found"] = True
                    r["breaches"].append({
                        "name":       b.get("Name",       ""),
                        "domain":     b.get("Domain",     ""),
                        "date":       b.get("BreachDate", ""),
                        "count":      b.get("PwnCount",   0),
                        "data_types": b.get("DataClasses", []),
                    })
            r["breach_count"] = len(r["breaches"])
        else:
            r["error"] = f"HTTP {res.status_code}"
    except Exception as e:
        r["error"] = str(e)
    return r

# ══════════════════════════════════════════
#              BREACH - ŞİFRE
# ══════════════════════════════════════════
def breach_password(password: str) -> dict:
    r = {"pwned": False, "count": 0, "error": None}
    try:
        sha1   = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        res = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"User-Agent": "M-OSINT/0.0.5", "Add-Padding": "true"},
            timeout=10
        )
        if res.status_code == 200:
            for line in res.text.splitlines():
                if ":" not in line:
                    continue
                h, cnt = line.split(":", 1)
                if h.strip().upper() == suffix:
                    r["pwned"] = True
                    r["count"] = int(cnt.strip())
                    break
        else:
            r["error"] = f"HTTP {res.status_code}"
    except Exception as e:
        r["error"] = str(e)
    return r

# ══════════════════════════════════════════
#              BREACH - TAM TARAMA
# ══════════════════════════════════════════
def breach_full(email: str) -> dict:
    r = {
        "email":      email,
        "leakcheck":  {},
        "hudsonrock": {},
        "hibp":       {},
        "summary": {
            "total_sources_checked": 3,
            "sources_with_data":     0,
            "total_breaches":        0,
            "infostealer_found":     False,
        }
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        fl = ex.submit(breach_leakcheck,  email)
        fh = ex.submit(breach_hudsonrock, email)
        fb = ex.submit(breach_hibp,       email)
        r["leakcheck"]  = fl.result()
        r["hudsonrock"] = fh.result()
        r["hibp"]       = fb.result()

    if r["leakcheck"].get("found"):
        r["summary"]["sources_with_data"] += 1
        r["summary"]["total_breaches"]    += r["leakcheck"]["breach_count"]
    if r["hudsonrock"].get("found"):
        r["summary"]["sources_with_data"] += 1
        r["summary"]["infostealer_found"]  = True
    if r["hibp"].get("found"):
        r["summary"]["sources_with_data"] += 1
        r["summary"]["total_breaches"]    += r["hibp"]["breach_count"]
    return r

# ══════════════════════════════════════════
#              TELEFON
# ══════════════════════════════════════════
COUNTRY_CODES = {
    "+90":  {"name": "Türkiye",           "iso": "TR", "flag": "🇹🇷"},
    "+1":   {"name": "ABD / Kanada",      "iso": "US", "flag": "🇺🇸"},
    "+44":  {"name": "İngiltere",         "iso": "GB", "flag": "🇬🇧"},
    "+49":  {"name": "Almanya",           "iso": "DE", "flag": "🇩🇪"},
    "+33":  {"name": "Fransa",            "iso": "FR", "flag": "🇫🇷"},
    "+7":   {"name": "Rusya",             "iso": "RU", "flag": "🇷🇺"},
    "+86":  {"name": "Çin",              "iso": "CN", "flag": "🇨🇳"},
    "+81":  {"name": "Japonya",           "iso": "JP", "flag": "🇯🇵"},
    "+82":  {"name": "Güney Kore",        "iso": "KR", "flag": "🇰🇷"},
    "+91":  {"name": "Hindistan",         "iso": "IN", "flag": "🇮🇳"},
    "+55":  {"name": "Brezilya",          "iso": "BR", "flag": "🇧🇷"},
    "+61":  {"name": "Avustralya",        "iso": "AU", "flag": "🇦🇺"},
    "+31":  {"name": "Hollanda",          "iso": "NL", "flag": "🇳🇱"},
    "+39":  {"name": "İtalya",           "iso": "IT", "flag": "🇮🇹"},
    "+34":  {"name": "İspanya",          "iso": "ES", "flag": "🇪🇸"},
    "+46":  {"name": "İsveç",            "iso": "SE", "flag": "🇸🇪"},
    "+47":  {"name": "Norveç",           "iso": "NO", "flag": "🇳🇴"},
    "+48":  {"name": "Polonya",           "iso": "PL", "flag": "🇵🇱"},
    "+380": {"name": "Ukrayna",           "iso": "UA", "flag": "🇺🇦"},
    "+966": {"name": "Suudi Arabistan",   "iso": "SA", "flag": "🇸🇦"},
    "+971": {"name": "BAE",              "iso": "AE", "flag": "🇦🇪"},
    "+972": {"name": "İsrail",           "iso": "IL", "flag": "🇮🇱"},
    "+20":  {"name": "Mısır",            "iso": "EG", "flag": "🇪🇬"},
    "+27":  {"name": "Güney Afrika",      "iso": "ZA", "flag": "🇿🇦"},
    "+52":  {"name": "Meksika",           "iso": "MX", "flag": "🇲🇽"},
    "+54":  {"name": "Arjantin",          "iso": "AR", "flag": "🇦🇷"},
    "+32":  {"name": "Belçika",          "iso": "BE", "flag": "🇧🇪"},
    "+41":  {"name": "İsviçre",          "iso": "CH", "flag": "🇨🇭"},
    "+43":  {"name": "Avusturya",         "iso": "AT", "flag": "🇦🇹"},
    "+351": {"name": "Portekiz",          "iso": "PT", "flag": "🇵🇹"},
    "+30":  {"name": "Yunanistan",        "iso": "GR", "flag": "🇬🇷"},
    "+40":  {"name": "Romanya",           "iso": "RO", "flag": "🇷🇴"},
    "+62":  {"name": "Endonezya",         "iso": "ID", "flag": "🇮🇩"},
    "+63":  {"name": "Filipinler",        "iso": "PH", "flag": "🇵🇭"},
    "+65":  {"name": "Singapur",          "iso": "SG", "flag": "🇸🇬"},
    "+66":  {"name": "Tayland",           "iso": "TH", "flag": "🇹🇭"},
    "+84":  {"name": "Vietnam",           "iso": "VN", "flag": "🇻🇳"},
    "+92":  {"name": "Pakistan",          "iso": "PK", "flag": "🇵🇰"},
    "+98":  {"name": "İran",             "iso": "IR", "flag": "🇮🇷"},
}

TR_OPERATORS = {
    "530": "Turkcell", "531": "Turkcell", "532": "Turkcell",
    "533": "Turkcell", "534": "Turkcell", "535": "Turkcell",
    "536": "Turkcell", "537": "Turkcell", "538": "Turkcell", "539": "Turkcell",
    "540": "Vodafone", "541": "Vodafone", "542": "Vodafone",
    "543": "Vodafone", "544": "Vodafone", "545": "Vodafone",
    "546": "Vodafone", "547": "Vodafone", "548": "Vodafone", "549": "Vodafone",
    "550": "Türk Telekom", "551": "Türk Telekom", "552": "Türk Telekom",
    "553": "Türk Telekom", "554": "Türk Telekom", "555": "Türk Telekom",
    "556": "Türk Telekom", "557": "Türk Telekom", "558": "Türk Telekom", "559": "Türk Telekom",
    "560": "Netgsm", "561": "Netgsm", "562": "Netgsm", "563": "Netgsm", "564": "Netgsm",
}

def phone_lookup(phone: str) -> dict:
    r = {
        "phone": phone, "valid": False,
        "country": "N/A", "country_iso": "N/A", "country_flag": "",
        "country_dial": "N/A", "local_number": "N/A",
        "carrier": "N/A", "line_type": "N/A",
        "formatted_international": "N/A", "formatted_local": "N/A",
        "whatsapp_link": None, "telegram_link": None,
        "risk_score": 0, "tags": [], "error": None
    }
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    if not cleaned.startswith("+"): cleaned = "+" + cleaned
    if not re.fullmatch(r"\+\d{7,15}", cleaned):
        r["error"] = "Geçersiz telefon formatı (7-15 rakam girin)"
        return r
    r["formatted_international"] = cleaned

    matched_code = None
    matched_info = None
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if cleaned.startswith(code):
            matched_code = code
            matched_info = COUNTRY_CODES[code]
            break

    if not matched_info:
        r["error"] = "Ülke kodu tanınamadı"
        return r

    r["valid"]        = True
    r["country"]      = matched_info["name"]
    r["country_iso"]  = matched_info["iso"]
    r["country_flag"] = matched_info["flag"]
    r["country_dial"] = matched_code

    local = cleaned[len(matched_code):]
    r["local_number"] = local

    if matched_code == "+90":
        if local.startswith("5") and len(local) == 10:
            r["line_type"] = "Mobil 📱"
            prefix = local[:3]
            r["carrier"] = TR_OPERATORS.get(prefix, "Bilinmeyen Operatör")
            r["formatted_local"] = f"0{local[:3]} {local[3:6]} {local[6:8]} {local[8:10]}"
        elif local.startswith(("2", "3", "4")):
            r["line_type"] = "Sabit Hat ☎️"
            r["carrier"]   = "Türk Telekom"
            r["formatted_local"] = f"0{local}"
        elif local.startswith("800"):
            r["line_type"] = "Ücretsiz 📞"
            r["tags"].append("Ücretsiz Hat")
    elif matched_code == "+1":
        r["line_type"] = "Kuzey Amerika"
        if len(local) >= 10:
            r["formatted_local"] = f"({local[:3]}) {local[3:6]}-{local[6:]}"
        else:
            r["formatted_local"] = local
    else:
        r["line_type"]      = "Uluslararası"
        r["formatted_local"] = local

    score = 0
    if r["country_iso"] in ["RU", "CN", "KP", "IR"]:
        score += 30
        r["tags"].append("Yüksek Riskli Ülke")
    if len(local) < 7:
        score += 20
        r["tags"].append("Kısa Numara")
    r["risk_score"] = min(score, 100)

    num_clean = cleaned.replace("+", "")
    r["whatsapp_link"] = f"https://wa.me/{num_clean}"
    r["telegram_link"] = f"https://t.me/+{num_clean}"
    return r

# ══════════════════════════════════════════
#              KULLANICI ADI
# ══════════════════════════════════════════
def username_search(username: str) -> dict:
    username = (username or "").strip().lstrip("@").strip()
    r = {"username": username, "found": [], "not_found": [], "blocked": [],
         "errors": [], "total_checked": 0, "total_found": 0, "total_blocked": 0}
    if not username or len(username) < 2:
        r["errors"].append({"platform": "-", "url": "", "status": None,
                             "error": "Kullanıcı adı çok kısa (min 2 karakter)"})
        return r
    # v0.0.3: test01 (10) + v0.0.2 (20) + yeni (16) = 46 platform
    # nf = sayfada varsa HESAP YOK demek olan imza metinler (küçük harf eşleşir)
    # need = sayfada MUTLAKA olması gereken imza (yoksa hesap yok sayılır)
    P = {
        "GitHub":      {"url": f"https://github.com/{username}", "nf": ["page not found"]},
        "X / Twitter": {"url": f"https://x.com/{username}", "nf": ["this account doesn", "account doesn", "page not found"]},
        "Instagram":   {"url": f"https://www.instagram.com/{username}/", "nf": ["sorry, this page isn't available", "page isn't available", "the link you followed may be broken"]},
        "TikTok":      {"url": f"https://www.tiktok.com/@{username}", "nf": [], "need": ['"uniqueid":"{u}"']},
        "YouTube":     {"url": f"https://www.youtube.com/@{username}", "nf": ["404 not found", "this channel does not exist", "this page isn't available"]},
        "Twitch":      {"url": f"https://www.twitch.tv/{username}", "nf": [], "need": ["- twitch</title>"]},
        "Reddit":      {"url": f"https://www.reddit.com/user/{username}/about.json", "nf": ['"error"', "not found"]},
        "Pinterest":   {"url": f"https://www.pinterest.com/{username}/", "nf": ["user not found", "page not found"]},
        "Spotify":     {"url": f"https://open.spotify.com/user/{username}", "nf": [], "manual": True},
        "Steam":       {"url": f"https://steamcommunity.com/id/{username}", "nf": ["the specified profile could not be found"]},
        "Telegram":    {"url": f"https://t.me/{username}", "nf": [], "need": ["tgme_page_photo"]},
        "LinkedIn":    {"url": f"https://www.linkedin.com/in/{username}", "nf": ["page not found", "couldn", "profile not found"]},
        "Snapchat":    {"url": f"https://www.snapchat.com/add/{username}", "nf": ["page not found", "couldn't find"]},
        "SoundCloud":  {"url": f"https://soundcloud.com/{username}", "nf": ["find that user", "not found", "404"]},
        "Patreon":     {"url": f"https://www.patreon.com/{username}", "nf": ["page not found", "couldn't find", "404"]},
        "Behance":     {"url": f"https://www.behance.net/{username}", "nf": ["page not found", "user not found"]},
        "Dribbble":    {"url": f"https://dribbble.com/{username}", "nf": ["whoops", "not found"]},
        "Keybase":     {"url": f"https://keybase.io/{username}", "nf": ["user not found", "not found"]},
        "DeviantArt":  {"url": f"https://www.deviantart.com/{username}", "nf": ["page not found", "user not found", "deactivated"]},
        "HackerRank":  {"url": f"https://www.hackerrank.com/{username}", "nf": [], "need": ["| hackerrank</title>"]},
        "Codeforces":  {"url": f"https://codeforces.com/profile/{username}", "nf": [], "need": ["{u} - codeforces</title>"]},
        "Medium":      {"url": f"https://medium.com/@{username}", "nf": ["page not found", "out of nothing", "user not found"]},
        "Vimeo":       {"url": f"https://vimeo.com/{username}", "nf": ["not found", "sorry"]},
        "Flickr":      {"url": f"https://www.flickr.com/people/{username}", "nf": ["page not found", "user not found"]},
        "Tumblr":      {"url": f"https://{username}.tumblr.com/", "nf": ["there's nothing here", "not found", "oops"]},
        "VK":          {"url": f"https://vk.com/{username}", "nf": ["page not found", "profile not found", "deleted or not yet created"]},
        "Facebook":    {"url": f"https://www.facebook.com/{username}", "nf": ["page isn't available", "page not found", "content isn't available"]},
        "GitLab":      {"url": f"https://gitlab.com/{username}", "nf": ["page not found"]},
        "Bitbucket":   {"url": f"https://bitbucket.org/{username}/", "nf": ["not found", "page not found"]},
        "NPM":         {"url": f"https://www.npmjs.com/~{username}", "nf": ["not found", "page not found"]},
        "PyPI":        {"url": f"https://pypi.org/user/{username}/", "nf": ["not found", "no such user"]},
        "Wattpad":     {"url": f"https://www.wattpad.com/user/{username}", "nf": ["user not found", "page not found"]},
        "Chess.com":   {"url": f"https://www.chess.com/member/{username}", "nf": ["page not found", "user not found"]},
        "Duolingo":    {"url": f"https://www.duolingo.com/2017-06-30/users?username={username}", "link": f"https://www.duolingo.com/profile/{username}", "nf": ['"users":[]', '"users": []']},
        "Gravatar":    {"url": f"https://en.gravatar.com/{username}.json", "nf": []},
        "About.me":    {"url": f"https://about.me/{username}", "nf": ["page not found", "not found"]},
        "ProductHunt": {"url": f"https://www.producthunt.com/@{username}", "nf": ["page not found", "not found", "oops"]},
        "HackerNews":  {"url": f"https://news.ycombinator.com/user?id={username}", "nf": ["no such user"]},
        "Replit":      {"url": f"https://replit.com/@{username}", "nf": ["not found", "couldn't find"]},
        "TryHackMe":   {"url": f"https://tryhackme.com/p/{username}", "nf": ["page not found", "not found"]},
        "OpenStreetMap": {"url": f"https://www.openstreetmap.org/user/{username}", "nf": ["no such user", "not found"]},
        "Fiverr":      {"url": f"https://www.fiverr.com/{username}", "nf": ["page not found", "user not found", "oops"]},
        "Kick":        {"url": f"https://kick.com/{username}", "nf": ["user not found", "not found", "oops"]},
        "Last.fm":     {"url": f"https://www.last.fm/user/{username}", "nf": ["user not found", "page not found"]},
        "CodePen":     {"url": f"https://codepen.io/{username}", "nf": ["not found", "page not found", "lost"]},
        "Kaggle":      {"url": f"https://www.kaggle.com/{username}", "nf": ["not found", "page not found"]},
    }
    r["total_checked"] = len(P)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
               "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
               "Accept-Language": "en-US,en;q=0.9"}

    # Bot duvarı / captcha sayfası imzaları -> engelli say (yanlış pozitif üretme)
    BLOCKED_PAGE = ["client challenge", "checking your browser",
                    "attention required! | cloudflare",
                    "unusual traffic from your computer network"]

    def chk(name, cfg):
        url = cfg["url"]
        show = cfg.get("link", url)
        if cfg.get("manual"):
            return {"platform": name, "url": show, "status": None, "found": False,
                    "blocked": True, "note": "manuel kontrol gerekli (giriş duvarı)"}
        try:
            res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            st = res.status_code
            # Bot koruması / rate-limit -> engelli say (yanlış pozitif üretme)
            if st in (429, 999) or (st == 403 and name in ("Instagram", "Facebook", "LinkedIn", "X / Twitter", "TikTok")):
                return {"platform": name, "url": show, "status": st, "found": False, "blocked": True}
            body = (res.text or "")
            if len(body) > 2000000: body = body[:2000000]
            body = body.lower()
            for m in BLOCKED_PAGE:
                if m in body:
                    return {"platform": name, "url": show, "status": st, "found": False, "blocked": True}
            if st == 404:
                return {"platform": name, "url": show, "status": st, "found": False}
            ul = username.lower()
            for m in cfg.get("nf", []):
                if m.replace("{u}", ul).lower() in body:
                    return {"platform": name, "url": show, "status": st, "found": False}
            need = cfg.get("need", [])
            if need:
                for m in need:
                    if m.replace("{u}", ul).lower() in body:
                        return {"platform": name, "url": show, "status": st, "found": True}
                return {"platform": name, "url": show, "status": st, "found": False}
            if st == 200:
                return {"platform": name, "url": show, "status": st, "found": True}
            return {"platform": name, "url": show, "status": st, "found": False}
        except Exception as e:
            return {"platform": name, "url": show, "status": None, "found": False, "error": str(e)[:200]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(chk, n, cf) for n, cf in P.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res.get("error"):     r["errors"].append(res)
            elif res.get("blocked"): r["blocked"].append(res)
            elif res["found"]:       r["found"].append(res)
            else:                    r["not_found"].append(res)

    r["found"]      = sorted(r["found"],     key=lambda x: x["platform"])
    r["not_found"]  = sorted(r["not_found"], key=lambda x: x["platform"])
    r["blocked"]    = sorted(r["blocked"],   key=lambda x: x["platform"])
    r["total_found"]   = len(r["found"])
    r["total_blocked"] = len(r["blocked"])
    return r

# ══════════════════════════════════════════
#              SUBDOMAIN
# ══════════════════════════════════════════
def subdomain_scan(domain: str) -> dict:
    r = {"domain": domain, "found": [], "not_found": 0,
         "total_checked": 0, "scan_time": None, "error": None}
    wordlist = [
        "www","mail","ftp","admin","api","dev","test","shop","blog","cdn",
        "m","mobile","app","beta","stage","staging","vpn","ssh","smtp","pop",
        "imap","ns1","ns2","dns","mx","webmail","cpanel","whm","portal","login",
        "secure","static","media","img","images","video","forum","community",
        "support","help","docs","wiki","status","monitor","dashboard","panel",
        "manage","git","svn","ci","jenkins","jira","gitlab","s3","files",
        "download","upload","api2","v1","v2","v3","internal","intranet","remote",
        "db","database","mysql","mongo","redis","elastic","search","auth","sso",
    ]
    r["total_checked"] = len(wordlist)
    start = datetime.now()

    def chk(sub):
        full = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(full)
            cname = None
            try:
                ans   = dns.resolver.resolve(full, "CNAME", lifetime=3)
                cname = str(ans[0])
            except: pass
            return {"subdomain": full, "ip": ip, "cname": cname, "found": True}
        except:
            return {"subdomain": full, "found": False}

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(chk, s) for s in wordlist]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res["found"]: r["found"].append(res)
            else:            r["not_found"] += 1

    r["found"]     = sorted(r["found"], key=lambda x: x["subdomain"])
    r["scan_time"] = str(datetime.now() - start)
    return r

# ══════════════════════════════════════════
#              URL ANALİZ
# ══════════════════════════════════════════
def url_analyze(url: str) -> dict:
    r = {
        "url": url, "final_url": None, "status_code": None,
        "title": None, "server": None, "powered_by": None,
        "content_type": None, "redirect_chain": [],
        "security_headers": {}, "technologies": [],
        "ip": None, "error": None
    }
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,*/*;q=0.8",
        "Accept-Language": "tr,en;q=0.9",
    }
    try:
        res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        r["final_url"]    = res.url
        r["status_code"]  = res.status_code
        r["server"]       = res.headers.get("Server",       "N/A")
        r["powered_by"]   = res.headers.get("X-Powered-By", "N/A")
        r["content_type"] = res.headers.get("Content-Type", "N/A")
        for resp in res.history:
            r["redirect_chain"].append({"url": resp.url, "status": resp.status_code})
        import re as _re
        t = _re.search(r"<title[^>]*>(.*?)</title>", res.text, _re.IGNORECASE | _re.DOTALL)
        r["title"] = t.group(1).strip()[:200] if t else "N/A"
        for h in ["Strict-Transport-Security", "Content-Security-Policy",
                  "X-Frame-Options", "X-Content-Type-Options",
                  "Referrer-Policy", "Permissions-Policy"]:
            r["security_headers"][h] = res.headers.get(h, None)
        tech = []
        body = res.text.lower()
        hs   = str(res.headers).lower()
        tech_map = {
            "WordPress":  ["wp-content", "wp-includes"],
            "React":      ["react", "__react"],
            "Vue.js":     ["vue.js", "__vue"],
            "Angular":    ["ng-version", "angular"],
            "jQuery":     ["jquery"],
            "Bootstrap":  ["bootstrap"],
            "Nginx":      ["nginx"],
            "Apache":     ["apache"],
            "Cloudflare": ["cloudflare", "cf-ray"],
            "Laravel":    ["laravel"],
            "Django":     ["csrfmiddlewaretoken"],
            "Next.js":    ["__next"],
            "PHP":        [".php"],
            "ASP.NET":    ["__viewstate"],
        }
        for name, patterns in tech_map.items():
            for p in patterns:
                if p in body or p in hs:
                    tech.append(name)
                    break
        r["technologies"] = list(set(tech))
        # v0.0.3 — güvenlik skoru
        try:
            score = 100
            if not str(r.get("final_url", "")).startswith("https://"):
                score -= 25
            missing = sum(1 for v in r["security_headers"].values() if not v)
            score -= missing * 10
            if r.get("server") not in (None, "N/A", ""):
                score -= 5
            score = max(5, min(100, score))
            r["security_score"] = score
            r["risk_level"] = "DÜŞÜK" if score >= 80 else ("ORTA" if score >= 55 else "YÜKSEK")
        except:
            r["security_score"] = None
            r["risk_level"] = "N/A"
        from urllib.parse import urlparse
        hostname = urlparse(res.url).hostname
        try:    r["ip"] = socket.gethostbyname(hostname)
        except: r["ip"] = "N/A"
    except Exception as e:
        r["error"] = str(e)
    return r

# ══════════════════════════════════════════
#              IP
# ══════════════════════════════════════════
def ip_lookup(ip: str) -> dict:
    r = {"ip": ip, "info": {}, "asn": {},
         "blacklist": {}, "map_link": None, "google_maps": None, "error": None}
    try:
        res = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"region,regionName,city,zip,lat,lon,timezone,isp,org,as,query",
            timeout=10
        )
        if res.status_code == 200:
            d = res.json()
            if d.get("status") == "success":
                r["info"] = {
                    "ip":           d.get("query"),
                    "hostname":     "N/A",
                    "city":         d.get("city",       "N/A"),
                    "region":       d.get("regionName", "N/A"),
                    "country":      d.get("country",    "N/A"),
                    "country_code": d.get("countryCode","N/A"),
                    "location":     f"{d.get('lat','')},{d.get('lon','')}",
                    "org":          d.get("org",        "N/A"),
                    "isp":          d.get("isp",        "N/A"),
                    "postal":       d.get("zip",        "N/A"),
                    "timezone":     d.get("timezone",   "N/A"),
                    "lat":          d.get("lat"),
                    "lon":          d.get("lon"),
                }
                asn_raw = d.get("as", "")
                if asn_raw:
                    pts = asn_raw.split(" ", 1)
                    r["asn"] = {
                        "asn": pts[0],
                        "org": pts[1] if len(pts) > 1 else "N/A"
                    }
                lat, lon = d.get("lat"), d.get("lon")
                if lat and lon:
                    r["map_link"]    = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=12"
                    r["google_maps"] = f"https://maps.google.com/?q={lat},{lon}"
            else:
                r["error"] = d.get("message", "Bilinmeyen hata")
    except Exception as e:
        r["error"] = str(e)

    try:
        url2 = f"https://ipinfo.io/{ip}/json"
        if IPINFO_TOKEN: url2 += f"?token={IPINFO_TOKEN}"
        r2 = requests.get(url2, timeout=8)
        if r2.status_code == 200 and r["info"]:
            r["info"]["hostname"] = r2.json().get("hostname", "N/A")
    except: pass

    bl  = {}
    rev = ".".join(reversed(ip.split(".")))
    for l in ["zen.spamhaus.org", "bl.spamcop.net", "b.barracudacentral.org"]:
        try:
            socket.gethostbyname(f"{rev}.{l}")
            bl[l] = True
        except socket.gaierror:
            bl[l] = False
        except:
            bl[l] = "error"
    r["blacklist"] = bl
    return r

# ══════════════════════════════════════════
#              DNS
# ══════════════════════════════════════════
def dns_lookup(domain: str) -> dict:
    r = {"domain": domain, "records": {}, "whois": {}, "error": None}
    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
        try:
            ans = dns.resolver.resolve(domain, rtype, lifetime=5)
            r["records"][rtype] = [str(x) for x in ans]
        except dns.resolver.NXDOMAIN:
            r["records"][rtype] = ["NXDOMAIN"]
        except dns.resolver.NoAnswer:
            r["records"][rtype] = []
        except Exception as e:
            r["records"][rtype] = [str(e)]
    try:
        w = whois.whois(domain)
        r["whois"] = {
            "registrar":       str(w.registrar)       if w.registrar       else "N/A",
            "creation_date":   str(w.creation_date)   if w.creation_date   else "N/A",
            "expiration_date": str(w.expiration_date) if w.expiration_date else "N/A",
            "name_servers":    list(w.name_servers)   if w.name_servers    else [],
            "emails":          w.emails               if w.emails          else [],
            "country":         str(w.country)         if w.country         else "N/A",
        }
    except Exception as e:
        r["whois"] = {"error": str(e)}
    return r

# ══════════════════════════════════════════
#              PORT
# ══════════════════════════════════════════
COMMON_PORTS = {
    21: "FTP",    22: "SSH",         23: "Telnet",      25: "SMTP",
    53: "DNS",    80: "HTTP",        110: "POP3",        143: "IMAP",
    443: "HTTPS", 445: "SMB",        3306: "MySQL",      3389: "RDP",
    5432: "PostgreSQL",              6379: "Redis",      8080: "HTTP-Alt",
    8443: "HTTPS-Alt",               27017: "MongoDB",   9200: "Elasticsearch",
    1433: "MSSQL",                   5900: "VNC",
}

def check_port(ip, port, timeout=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        if s.connect_ex((ip, port)) == 0:
            s.close()
            banner = ""
            try:
                s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s2.settimeout(2)
                s2.connect((ip, port))
                if port in [80, 8080]:
                    s2.send(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = s2.recv(512).decode("utf-8", errors="ignore").strip()[:150]
                s2.close()
            except: pass
            return {"port": port, "open": True,
                    "service": COMMON_PORTS.get(port, "Unknown"), "banner": banner}
        s.close()
    except: pass
    return {"port": port, "open": False}

def port_scan(host: str, port_range: str = "common") -> dict:
    r = {"host": host, "ip": None, "open_ports": [],
         "closed_count": 0, "scan_time": None, "error": None}
    start = datetime.now()
    try:
        r["ip"] = socket.gethostbyname(host)
    except Exception as e:
        r["error"] = str(e)
        return r

    if port_range == "common":     ports = list(COMMON_PORTS.keys())
    elif port_range == "top100":   ports = list(range(1, 101))
    elif port_range == "top1000":  ports = list(range(1, 1001))
    else:
        try:
            s, e = map(int, port_range.split("-"))
            if not (1 <= s <= e <= 65535) or e - s >= 1024:
                raise ValueError("Port aralığı 1-65535 arasında ve en fazla 1024 port olmalıdır")
            ports = list(range(s, e + 1))
        except Exception as exc:
            r["error"] = str(exc) if "Port aralığı" in str(exc) else "Geçersiz port aralığı"
            return r

    open_ports, closed = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as ex:
        futures = {ex.submit(check_port, r["ip"], p): p for p in ports}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res["open"]: open_ports.append(res)
            else:           closed += 1

    r["open_ports"]   = sorted(open_ports, key=lambda x: x["port"])
    r["closed_count"] = closed
    r["scan_time"]    = str(datetime.now() - start)
    return r

# ══════════════════════════════════════════
#              EMAIL
# ══════════════════════════════════════════
def email_check(email: str) -> dict:
    r = {
        "email": email, "format_valid": False, "domain_valid": False,
        "mx_records": [], "disposable": False, "free_provider": False,
        "gravatar": {}, "social_guess": {}, "error": None
    }
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        r["error"] = "Geçersiz format"
        return r
    r["format_valid"] = True
    domain = email.split("@")[1]
    try:
        mx = dns.resolver.resolve(domain, "MX", lifetime=5)
        r["mx_records"]   = [str(x.exchange) for x in mx]
        r["domain_valid"] = True
    except:
        r["domain_valid"] = False

    r["disposable"]    = domain.lower() in [
        "tempmail.com", "guerrillamail.com", "mailinator.com", "yopmail.com"]
    r["free_provider"] = domain.lower() in [
        "gmail.com", "yahoo.com", "hotmail.com",
        "outlook.com", "yandex.com", "protonmail.com"]
    try:
        h  = hashlib.md5(email.lower().encode()).hexdigest()
        gr = requests.get(f"https://www.gravatar.com/avatar/{h}?d=404", timeout=5)
        r["gravatar"] = {
            "exists": gr.status_code == 200,
            "url":    f"https://www.gravatar.com/avatar/{h}"
        }
    except:
        r["gravatar"] = {"exists": False, "url": None}

    u = email.split("@")[0]
    r["social_guess"] = {
        "github":    f"https://github.com/{u}",
        "twitter":   f"https://twitter.com/{u}",
        "instagram": f"https://instagram.com/{u}",
        "reddit":    f"https://reddit.com/user/{u}",
    }
    return r

# ══════════════════════════════════════════
#              SSL SERTİFİKA ANALİZİ (v0.0.3)
# ══════════════════════════════════════════
def ssl_check(host: str) -> dict:
    r = {"host": host, "hostname": None, "port": 443, "ip": None, "reachable": False,
         "tls_version": None, "cipher": None, "cert": {}, "checks": {}, "grade": "N/A", "error": None}
    try:
        h = (host or "").strip()
        if "://" in h:
            try: h = urlparse(h).hostname or h
            except: pass
        h = h.split("/")[0].strip()
        port = 443
        if ":" in h and not h.startswith("["):
            parts = h.rsplit(":", 1)
            if parts[1].isdigit():
                h, port = parts[0], int(parts[1])
        if not h:
            r["error"] = "Geçersiz host"
            return r
        r["hostname"] = h
        r["port"] = port
        try:
            r["ip"] = socket.gethostbyname(h)
        except Exception as e:
            r["error"] = f"DNS çözülemedi: {e}"
            return r
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((h, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=h) as ss:
                r["reachable"] = True
                try: r["tls_version"] = ss.version()
                except: pass
                try:
                    cip = ss.cipher()
                    if cip: r["cipher"] = f"{cip[0]} ({cip[1]})"
                except: pass
                cert = ss.getpeercert(binary_form=False) or {}
                if not cert:
                    # Bazı OpenSSL/Python kombinasyonlarında dict boş gelir -> DER yedeği
                    try:
                        import tempfile
                        der = ss.getpeercert(binary_form=True)
                        if der:
                            pem = ssl.DER_cert_to_PEM_cert(der)
                            with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as tf:
                                tf.write(pem)
                                tpath = tf.name
                            try: cert = ssl._ssl._test_decode_cert(tpath) or {}
                            finally:
                                try: os.remove(tpath)
                                except: pass
                    except: pass
                def _flat(tup):
                    out = {}
                    try:
                        for item in tup:
                            for k, v in item: out[k] = v
                    except: pass
                    return out
                subj = _flat(cert.get("subject", ()))
                issr = _flat(cert.get("issuer", ()))
                sans = []
                try:
                    for typ, val in cert.get("subjectAltName", []):
                        if typ == "DNS": sans.append(val)
                except: pass
                nb_raw, na_raw = cert.get("notBefore"), cert.get("notAfter")
                nb_dt = na_dt = None
                for fmt in ("%b %d %H:%M:%S %Y %Z", "%b %d %H:%M:%S %Y %Z"):
                    try:
                        if nb_raw and not nb_dt: nb_dt = datetime.strptime(" ".join(nb_raw.split()), fmt)
                    except: pass
                    try:
                        if na_raw and not na_dt: na_dt = datetime.strptime(" ".join(na_raw.split()), fmt)
                    except: pass
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                days_left = (na_dt - now).days if na_dt else None
                expired = days_left is not None and days_left < 0
                self_signed = bool(subj and issr and subj == issr)
                def _match(pat, hst):
                    pat, hst = pat.lower(), hst.lower()
                    if pat == hst: return True
                    if pat.startswith("*."):
                        return hst.endswith(pat[1:]) and hst.count(".") == pat.count(".")
                    return False
                cn = subj.get("commonName", "")
                names = ([cn] if cn else []) + sans
                host_ok = any(_match(n, h) for n in names) if names else False
                r["cert"] = {"subject": subj, "issuer": issr, "common_name": cn or "N/A",
                             "sans": sans[:30], "san_count": len(sans),
                             "not_before": nb_raw or "N/A", "not_after": na_raw or "N/A",
                             "days_left": days_left, "serial": cert.get("serialNumber", "N/A")}
                r["checks"] = {"expired": expired, "self_signed": self_signed, "hostname_match": host_ok,
                               "tls_ok": (r["tls_version"] in ("TLSv1.2", "TLSv1.3"))}
                if expired: g = "F"
                elif self_signed: g = "D"
                elif not host_ok: g = "C"
                elif r["tls_version"] == "TLSv1.3" and (days_left or 0) > 30: g = "A+"
                elif r["tls_version"] in ("TLSv1.2", "TLSv1.3") and (days_left or 0) > 14: g = "A"
                elif (days_left or 0) <= 14: g = "B"
                else: g = "B"
                r["grade"] = g
    except Exception as e:
        r["error"] = str(e)[:300]
    return r

# ══════════════════════════════════════════
#              HASH ANALİZ + ÇÖZÜCÜ (v0.0.3)
# ══════════════════════════════════════════
def hash_analyze(value: str) -> dict:
    v = (value or "").strip()
    r = {"input": v, "is_hash": False, "possible_types": [], "length": len(v),
         "generated": {}, "lookup": {"found": False, "plain": None, "info": None, "source": None}, "error": None}
    if not v:
        r["error"] = "Boş giriş"
        return r
    low = v.lower()
    is_hex = re.fullmatch(r"[0-9a-f]+", low) is not None
    if re.match(r"^\$2[aby]\$\d{2}\$.{53}$", v):
        r["possible_types"] = ["bcrypt"]
        r["is_hash"] = True
    elif v.startswith("$1$"):
        r["possible_types"] = ["md5-crypt"]; r["is_hash"] = True
    elif v.startswith("$5$"):
        r["possible_types"] = ["sha256-crypt"]; r["is_hash"] = True
    elif v.startswith("$6$"):
        r["possible_types"] = ["sha512-crypt"]; r["is_hash"] = True
    elif is_hex:
        L = len(v)
        if L == 16:   r["possible_types"] = ["MD5 (kısaltılmış)", "MySQL OLD_PASSWORD"]
        elif L == 32: r["possible_types"] = ["MD5", "NTLM", "MD4"]
        elif L == 40: r["possible_types"] = ["SHA-1"]
        elif L == 56: r["possible_types"] = ["SHA-224"]
        elif L == 64: r["possible_types"] = ["SHA-256"]
        elif L == 96: r["possible_types"] = ["SHA-384"]
        elif L == 128: r["possible_types"] = ["SHA-512", "Whirlpool"]
        else: r["possible_types"] = ["Bilinmeyen hex"]
        r["is_hash"] = L in (16, 32, 40, 56, 64, 96, 128)
    else:
        r["possible_types"] = ["Düz metin (hash değil)"]
        try:
            b = v.encode()
            r["generated"] = {"md5": hashlib.md5(b).hexdigest(), "sha1": hashlib.sha1(b).hexdigest(),
                              "sha256": hashlib.sha256(b).hexdigest(), "sha512": hashlib.sha512(b).hexdigest()}
        except: pass
        return r
    if r["is_hash"] and is_hex:
        # 1) Yerel zayıf parola sözlüğü (hızlı, çevrimdışı)
        try:
            weak = ["123456","password","123456789","12345678","12345","1234567","1234567890","qwerty",
                    "abc123","password1","123123","admin","letmein","welcome","monkey","dragon","football",
                    "baseball","superman","trustno1","hello","charlie","aa123456","donald","password123",
                    "qwerty123","michael","jesus","computer","love","secret","jordan","test","passw0rd",
                    "batman","master","sunshine","shadow","ashley","mickey","daniel","jessica","killer",
                    "hunter","freedom","whatever","thomas","andrew","tigger","robert","access","buster",
                    "soccer","hockey","george","sexy","andrea","falcon","jennifer","hunter2",
                    "thunder","merlin","harley","ranger","taylor","melissa","joshua","maggie","starwars",
                    "silver","william","corvette","chelsea","diablo","qazwsx","princess","solo","loveme",
                    "zaq1zaq1","hello123","freedom1","jordan23","qwertyuiop","654321","1qaz2wsx",
                    "aa12345678","abc123456","princess1","turkiye","turkey","istanbul","ankara","mehmet",
                    "mustafa","ahmet","ayse","fatma","1234qwer"]
            algos = []
            if len(v) == 32: algos = ["md5"]
            elif len(v) == 40: algos = ["sha1"]
            elif len(v) == 64: algos = ["sha256"]
            for w in weak:
                b = w.encode()
                for a in algos:
                    hh = {"md5": hashlib.md5, "sha1": hashlib.sha1, "sha256": hashlib.sha256}[a](b).hexdigest()
                    if hh == low:
                        r["lookup"] = {"found": True, "plain": w, "info": None,
                                       "source": "yerel sözlük (zayıf parola)"}
                        return r
        except: pass
        # 2) CIRCL hashlookup (bilinen dosya / zararlı istihbaratı)
        try:
            algo = {32: "md5", 40: "sha1", 64: "sha256"}.get(len(v))
            if algo:
                res = requests.get(f"https://hashlookup.circl.lu/lookup/{algo}/{low}",
                    headers={"Accept": "application/json", "User-Agent": "M-OSINT/0.0.5"}, timeout=10)
                if res.status_code == 200:
                    try: d = res.json()
                    except: d = {}
                    if isinstance(d, dict) and d:
                        parts = []
                        if d.get("FileName"): parts.append(f"Dosya: {d.get('FileName')}")
                        if d.get("KnownMalicious"): parts.append(f"Zararlı: {d.get('KnownMalicious')}")
                        if d.get("FileSize"): parts.append(f"Boyut: {d.get('FileSize')}B")
                        for k in ("MD5", "SHA-1", "SHA-256"):
                            if d.get(k): parts.append(f"{k}: {str(d.get(k))[:32]}…")
                        r["lookup"] = {"found": True, "plain": None,
                                       "info": " • ".join(parts)[:400] if parts else "CIRCL veritabanında kayıtlı hash",
                                       "source": "hashlookup.circl.lu (CIRCL)"}
                        return r
        except: pass
    return r

# ══════════════════════════════════════════
#              CERT TRANSPARENCY (v0.0.3)
# ══════════════════════════════════════════
def crtsh_lookup(domain: str) -> dict:
    d0 = (domain or "").strip().lower()
    r = {"domain": d0, "clean_domain": None, "total_certs": 0, "subdomain_count": 0,
         "subdomains": [], "certs": [], "error": None}
    try:
        d = d0
        if "://" in d:
            try: d = urlparse(d).hostname or d
            except: pass
        d = d.split("/")[0].split(":")[0].strip()
        if d.startswith("www."): d = d[4:]
        if not d or "." not in d:
            r["error"] = "Geçersiz domain"
            return r
        r["clean_domain"] = d
        url = f"https://crt.sh/?q=%25.{d}&output=json"
        data = None
        last_err = None
        for attempt in range(3):
            try:
                res = requests.get(url, headers={"User-Agent": "M-OSINT/0.0.5", "Accept": "application/json"}, timeout=25)
                if res.status_code == 200:
                    try:
                        data = res.json()
                        break
                    except:
                        last_err = "crt.sh yanıtı çözülemedi (tekrar deneniyor)"
                else:
                    last_err = f"crt.sh HTTP {res.status_code}"
            except Exception as e:
                last_err = str(e)[:120]
            if attempt < 2:
                time.sleep(2)
        if data is None:
            r["error"] = f"{last_err} — crt.sh bazen yoğun olur, tekrar deneyin"
            return r
        if not isinstance(data, list):
            r["error"] = "crt.sh beklenmeyen yanıt"
            return r
        r["total_certs"] = len(data)
        subs = set()
        certs = []
        for c in data[:500]:
            nv = str(c.get("name_value", "") or "")
            for line in nv.splitlines():
                x = line.strip().lower()
                if not x or "*" in x or " " in x: continue
                if x == d or x.endswith("." + d): subs.add(x)
            if len(certs) < 25:
                certs.append({"common_name": c.get("common_name", "N/A"),
                              "issuer": str(c.get("issuer_name", "N/A"))[:120],
                              "not_before": c.get("not_before", "N/A"),
                              "not_after": c.get("not_after", "N/A")})
        r["subdomains"] = sorted(subs)[:500]
        r["subdomain_count"] = len(subs)
        r["certs"] = certs
    except Exception as e:
        r["error"] = str(e)[:300]
    return r

# ══════════════════════════════════════════
#              MAC VENDOR
# ══════════════════════════════════════════
def mac_lookup(mac: str) -> dict:
    r = {"mac": mac, "normalized": None, "vendor": None,
         "is_local": False, "is_multicast": False, "error": None}
    clean = re.sub(r"[^0-9A-Fa-f]", "", mac or "")
    if len(clean) < 6:
        r["error"] = "Geçersiz MAC adresi"
        return r
    clean = clean[:12].upper().ljust(12, "0")
    r["normalized"] = ":".join(clean[i:i+2] for i in range(0, 12, 2))
    try:
        first_octet = int(clean[0:2], 16)
        r["is_local"]     = bool(first_octet & 0b00000010)
        r["is_multicast"] = bool(first_octet & 0b00000001)
    except:
        pass
    try:
        res = requests.get(f"https://api.macvendors.com/{r['normalized']}", timeout=10)
        if res.status_code == 200 and res.text and "not found" not in res.text.lower():
            r["vendor"] = res.text.strip()
        elif res.status_code == 404:
            r["vendor"] = None
        elif res.status_code == 429:
            r["error"] = "Rate limit — biraz sonra tekrar deneyin"
    except Exception as e:
        r["error"] = str(e)[:200]
    return r

# ══════════════════════════════════════════
#              ENCODE / DECODE TOOLKIT
# ══════════════════════════════════════════
def encode_decode(mode: str, text: str) -> dict:
    import base64, urllib.parse, binascii
    r = {"mode": mode, "input": text, "output": None, "error": None}
    try:
        if mode == "b64_encode":
            r["output"] = base64.b64encode(text.encode("utf-8")).decode("ascii")
        elif mode == "b64_decode":
            pad = text + "=" * (-len(text) % 4)
            r["output"] = base64.b64decode(pad).decode("utf-8", errors="replace")
        elif mode == "url_encode":
            r["output"] = urllib.parse.quote(text, safe="")
        elif mode == "url_decode":
            r["output"] = urllib.parse.unquote(text)
        elif mode == "hex_encode":
            r["output"] = text.encode("utf-8").hex()
        elif mode == "hex_decode":
            clean = re.sub(r"[^0-9A-Fa-f]", "", text)
            r["output"] = binascii.unhexlify(clean).decode("utf-8", errors="replace")
        elif mode == "rot13":
            r["output"] = codecs.encode(text, "rot_13")
        else:
            r["error"] = "Bilinmeyen mod"
    except Exception as e:
        r["error"] = str(e)[:200]
    return r

# ══════════════════════════════════════════
#              v0.0.5 ARAÇLARI
# ══════════════════════════════════════════
def _clean_domain(value: str) -> str:
    """URL veya alan adından doğrulanmış bir hostname döndürür."""
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else "https://" + value)
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    return host if re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", host) else ""

def email_auth_check(domain: str) -> dict:
    """SPF, DMARC ve MX kayıtlarını tek istekte görünür kılar."""
    domain = _clean_domain(domain)
    r = {"domain": domain, "mx": [], "spf": None, "dmarc": None,
         "ns": [], "score": 0, "error": None}
    if not domain:
        r["error"] = "Geçerli bir alan adı girin"
        return r
    def query(name, record):
        try:
            return [str(x).strip('"') for x in dns.resolver.resolve(name, record, lifetime=5)]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return []
        except Exception:
            return []
    r["mx"] = query(domain, "MX")
    r["ns"] = query(domain, "NS")
    txt = query(domain, "TXT")
    dmarc = query("_dmarc." + domain, "TXT")
    r["spf"] = next((v for v in txt if v.lower().startswith("v=spf1")), None)
    r["dmarc"] = next((v for v in dmarc if v.lower().startswith("v=dmarc1")), None)
    r["score"] = (40 if r["mx"] else 0) + (30 if r["spf"] else 0) + (30 if r["dmarc"] else 0)
    return r

def web_footprint(target: str) -> dict:
    """robots.txt ve sitemap.xml ile yayımlanmış web yüzeyini keşfeder."""
    domain = _clean_domain(target)
    r = {"domain": domain, "robots_found": False, "sitemaps": [],
         "urls": [], "error": None}
    if not domain:
        r["error"] = "Geçerli bir URL veya alan adı girin"
        return r
    base = "https://" + domain
    try:
        response = requests.get(base + "/robots.txt", timeout=10, allow_redirects=True,
                                headers={"User-Agent": "M-OSINT/0.0.5"})
        if response.status_code == 200:
            r["robots_found"] = True
            r["sitemaps"] = list(dict.fromkeys(re.findall(r"(?im)^sitemap:\s*(\S+)", response.text)))[:10]
            r["urls"] = list(dict.fromkeys(re.findall(r"(?im)^(?:allow|disallow):\s*(\S+)", response.text)))[:100]
        elif response.status_code not in (401, 403, 404):
            r["error"] = f"robots.txt HTTP {response.status_code}"
    except requests.RequestException as e:
        r["error"] = f"İstek hatası: {e}"
    if not r["sitemaps"]:
        r["sitemaps"] = [base + "/sitemap.xml"]
    return r

def security_txt_check(target: str) -> dict:
    """RFC 9116 security.txt dosyasını kontrol eder."""
    domain = _clean_domain(target)
    r = {"domain": domain, "found": False, "url": None, "fields": {}, "error": None}
    if not domain:
        r["error"] = "Geçerli bir URL veya alan adı girin"
        return r
    for path in ("/.well-known/security.txt", "/security.txt"):
        url = "https://" + domain + path
        try:
            response = requests.get(url, timeout=10, allow_redirects=True,
                                    headers={"User-Agent": "M-OSINT/0.0.5"})
            if response.status_code != 200:
                continue
            fields = {}
            for key, value in re.findall(r"(?im)^([a-z-]+):\s*(.+)$", response.text):
                fields.setdefault(key.title(), []).append(value.strip())
            r.update({"found": True, "url": response.url, "fields": fields})
            return r
        except requests.RequestException:
            continue
    r["error"] = "security.txt bulunamadı"
    return r

def ioc_extract(text: str) -> dict:
    """Metinden IOC'leri çıkarır; ağ isteği yapmaz."""
    text = (text or "")[:50000]
    if not text.strip():
        return {"error": "Analiz edilecek metin girin"}
    def unique(values):
        return list(dict.fromkeys(values))[:100]
    urls = unique(re.findall(r"https?://[^\s<>\"']+", text, re.I))
    emails = unique(re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.I))
    ips = unique([value for value in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
                  if all(int(part) <= 255 for part in value.split("."))])
    hashes = unique(re.findall(r"\b[a-fA-F0-9]{32}(?:[a-fA-F0-9]{8})?(?:[a-fA-F0-9]{24})?\b", text))
    domains = unique(re.findall(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", text, re.I))
    return {"urls": urls, "emails": emails, "ips": ips, "hashes": hashes,
            "domains": domains, "total": sum(map(len, (urls, emails, ips, hashes, domains)))}

def password_strength(password: str) -> dict:
    """Şifreyi yerelde puanlar; değer saklanmaz veya gönderilmez."""
    password = password or ""
    if not password:
        return {"error": "Şifre girin"}
    classes = sum((any(c.islower() for c in password), any(c.isupper() for c in password),
                   any(c.isdigit() for c in password), any(not c.isalnum() for c in password)))
    charset = 26 * any(c.islower() for c in password) + 26 * any(c.isupper() for c in password) + 10 * any(c.isdigit() for c in password) + 33 * any(not c.isalnum() for c in password)
    entropy = round(len(password) * math.log2(max(charset, 1)), 1)
    weak = ["password", "123456", "qwerty", "admin", "letmein"]
    issues = []
    if len(password) < 12: issues.append("12 karakterden kısa")
    if classes < 3: issues.append("Karakter çeşitliliği düşük")
    if any(token in password.lower() for token in weak): issues.append("Yaygın bir ifade içeriyor")
    score = min(100, len(password) * 4 + classes * 12 + (12 if entropy >= 60 else 0) - len(issues) * 12)
    level = "Güçlü" if score >= 75 else "Orta" if score >= 45 else "Zayıf"
    return {"length": len(password), "classes": classes, "entropy_bits": entropy,
            "score": max(0, score), "level": level, "issues": issues,
            "note": "Şifre yalnızca tarayıcı ile yerel servis arasında işlenir; kaydedilmez."}


# ══════════════════════════════════════════
#              HTML
# ══════════════════════════════════════════
HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>M-OSINT """ + VERSION + """</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.0/socket.io.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0d0d;--bg2:#141414;--bg3:#1c1c1c;--bg4:#222;
  --border:#252525;--border2:#2e2e2e;
  --accent:#3b82f6;--accent2:#2563eb;
  --green:#22c55e;--red:#ef4444;--yellow:#eab308;
  --orange:#f97316;--purple:#a855f7;--cyan:#06b6d4;
  --text:#e5e7eb;--text2:#9ca3af;--text3:#6b7280;
}
html,body{height:100%;overflow:hidden;background:var(--bg)}
body{color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;display:flex;flex-direction:column}

/* NAV */
#nav{
  height:54px;background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 20px;gap:2px;flex-shrink:0;z-index:100;
}
.nav-logo{
  font-size:16px;font-weight:900;letter-spacing:3px;margin-right:32px;
  background:linear-gradient(135deg,#3b82f6,#06b6d4);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.nav-links{display:flex;align-items:center;gap:1px;flex:1;flex-wrap:nowrap;overflow-x:auto}
.nav-links::-webkit-scrollbar{height:0}
.nl{
  display:flex;align-items:center;gap:5px;padding:6px 11px;
  color:var(--text3);font-size:12px;font-weight:500;cursor:pointer;
  border-radius:6px;transition:all .15s;white-space:nowrap;border:1px solid transparent;
}
.nl:hover{color:var(--text);background:var(--bg3)}
.nl.active{color:var(--accent);background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.2)}
.nl i{font-size:11px}
.nav-right{display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0}
.nbadge{
  background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);
  color:var(--accent);padding:3px 9px;border-radius:20px;font-size:11px;font-weight:600;
}
.nbadge2{color:var(--text3);font-size:11px;font-family:monospace}

/* LAYOUT */
#wrap{flex:1;overflow:hidden;display:flex;flex-direction:column}
#body{flex:1;overflow-y:auto;padding:20px}
#body::-webkit-scrollbar{width:4px}
#body::-webkit-scrollbar-track{background:var(--bg)}
#body::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

/* PAGES */
.page{display:none}.page.active{display:block}

/* HERO */
.hero{text-align:center;padding:44px 0 32px}
.hero h1{
  font-size:34px;font-weight:800;margin-bottom:8px;
  background:linear-gradient(135deg,#fff 30%,#6b7280);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.hero p{color:var(--text3);font-size:13px;margin-bottom:4px}
.hero small{color:var(--text3);font-size:11px;opacity:.6}
.searchbox{
  max-width:620px;margin:24px auto 0;
  background:var(--bg2);border:1px solid var(--border2);
  border-radius:10px;padding:4px;display:flex;gap:4px;
  transition:border-color .2s;
}
.searchbox:focus-within{border-color:rgba(59,130,246,.4)}
.searchbox input{
  flex:1;background:none;border:none;outline:none;
  color:var(--text);font-size:13px;padding:9px 12px;font-family:inherit;
}
.searchbox input::placeholder{color:var(--text3)}
.searchbox select{
  background:var(--bg3);border:1px solid var(--border);color:var(--text);
  padding:7px 10px;border-radius:7px;font-size:12px;outline:none;cursor:pointer;
}
.searchbox button{
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  color:#fff;border:none;padding:9px 18px;border-radius:7px;
  font-size:12px;font-weight:700;cursor:pointer;transition:all .2s;white-space:nowrap;
}
.searchbox button:hover{opacity:.88;box-shadow:0 0 18px rgba(59,130,246,.3)}

/* STATS */
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px}
.stat-c{
  background:var(--bg2);border:1px solid var(--border);border-radius:9px;
  padding:14px;display:flex;align-items:center;gap:10px;
}
.stat-ic{
  width:36px;height:36px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;
}
.stat-n{font-size:20px;font-weight:800;line-height:1}
.stat-l{font-size:10px;color:var(--text3);margin-top:2px;text-transform:uppercase;letter-spacing:.8px}

/* MOD GRID */
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
.mcard{
  background:var(--bg2);border:1px solid var(--border);border-radius:9px;
  padding:16px;cursor:pointer;transition:all .18s;position:relative;overflow:hidden;
}
.mcard:hover{border-color:rgba(59,130,246,.35);transform:translateY(-2px);
  box-shadow:0 4px 20px rgba(59,130,246,.08)}
.mcard .mi{font-size:22px;margin-bottom:8px}
.mcard .mn{font-size:12px;font-weight:700;margin-bottom:3px}
.mcard .md{font-size:11px;color:var(--text3);line-height:1.5}

/* SECTION */
.sec{font-size:11px;font-weight:700;color:var(--text3);text-transform:uppercase;
  letter-spacing:1.5px;margin:16px 0 10px;display:flex;align-items:center;gap:8px}
.sec::after{content:'';flex:1;height:1px;background:var(--border)}

/* TOOL HEADER */
.th{background:var(--bg2);border:1px solid var(--border);border-radius:10px;
  padding:18px 20px;margin-bottom:14px}
.th h2{font-size:16px;font-weight:700;margin-bottom:3px;display:flex;align-items:center;gap:8px}
.th p{font-size:12px;color:var(--text3)}
.irow{display:flex;gap:7px;margin-top:12px}
.mi2{
  flex:1;background:var(--bg3);border:1px solid var(--border);color:var(--text);
  padding:9px 12px;border-radius:7px;font-size:13px;font-family:inherit;
  outline:none;transition:border-color .2s;
}
.mi2:focus{border-color:rgba(59,130,246,.5)}
.msel{
  background:var(--bg3);border:1px solid var(--border);color:var(--text);
  padding:9px 10px;border-radius:7px;font-size:12px;outline:none;cursor:pointer;
}
.mbtn{
  background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border:none;
  padding:9px 18px;border-radius:7px;font-size:12px;font-weight:700;
  cursor:pointer;transition:all .2s;white-space:nowrap;font-family:inherit;
}
.mbtn:hover{opacity:.88;box-shadow:0 0 14px rgba(59,130,246,.3)}
.mbtn:disabled{opacity:.35;cursor:not-allowed}
.mbtn.r{background:linear-gradient(135deg,#dc2626,#b91c1c)}

/* CARDS */
.rc{background:var(--bg2);border:1px solid var(--border);border-radius:9px;padding:16px}
.rh{display:flex;align-items:center;gap:7px;margin-bottom:12px;
  padding-bottom:10px;border-bottom:1px solid var(--border)}
.rh .ri{font-size:13px}
.rh .rt{font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:1px;color:var(--text2)}
.rh .rb{margin-left:auto}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}

/* SOURCE CARDS */
.scards{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}
.sc{background:var(--bg2);border:1px solid var(--border);border-radius:9px;
  padding:14px;text-align:center}
.sc .sn{font-size:26px;font-weight:900;margin-bottom:3px}
.sc .sl{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.8px}

/* TABLE */
.mt{width:100%;border-collapse:collapse;font-size:12px}
.mt th{padding:7px 10px;color:var(--text3);font-size:10px;text-transform:uppercase;
  letter-spacing:.8px;text-align:left;border-bottom:1px solid var(--border);
  background:var(--bg3);font-weight:600}
.mt td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.03);vertical-align:top}
.mt tr:last-child td{border-bottom:none}
.mt tr:hover td{background:rgba(255,255,255,.015)}
.mt td.k{color:var(--text3);width:36%;font-size:11px}

/* BADGES */
.b{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;
  border-radius:5px;font-size:11px;font-weight:600}
.br{background:rgba(239,68,68,.1);color:#ef4444;border:1px solid rgba(239,68,68,.2)}
.bg{background:rgba(34,197,94,.1);color:#22c55e;border:1px solid rgba(34,197,94,.2)}
.bb{background:rgba(59,130,246,.1);color:#60a5fa;border:1px solid rgba(59,130,246,.2)}
.by{background:rgba(234,179,8,.1);color:#eab308;border:1px solid rgba(234,179,8,.2)}
.bo{background:rgba(249,115,22,.1);color:#f97316;border:1px solid rgba(249,115,22,.2)}
.bp{background:rgba(168,85,247,.1);color:#a855f7;border:1px solid rgba(168,85,247,.2)}
.bc{background:rgba(6,182,212,.1);color:#06b6d4;border:1px solid rgba(6,182,212,.2)}
.bgr{background:rgba(107,114,128,.1);color:#9ca3af;border:1px solid rgba(107,114,128,.2)}

/* LOADER */
.ldr{display:none;padding:28px;text-align:center}
.ldr-i{display:inline-flex;align-items:center;gap:10px;color:var(--text3);font-size:13px}
.spin{width:16px;height:16px;border:2px solid var(--border2);
  border-top-color:var(--accent);border-radius:50%;
  animation:spin .7s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}

/* TERMINAL */
.term{background:#080808;border:1px solid var(--border);border-radius:9px;
  padding:14px;height:360px;overflow-y:auto;font-size:12px;
  font-family:'Cascadia Code','Fira Code','Courier New',monospace;line-height:1.75}
.term::-webkit-scrollbar{width:3px}
.term::-webkit-scrollbar-thumb{background:var(--border2)}

/* PLATFORM GRID */
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:7px;margin-top:8px}
.pi{background:var(--bg3);border:1px solid var(--border);border-radius:7px;
  padding:9px 11px;display:flex;align-items:center;gap:7px;font-size:12px}
.pi.found{border-color:rgba(34,197,94,.3)}
.pi.found a{color:var(--green);text-decoration:none;font-weight:600}
.pi.found a:hover{text-decoration:underline}
.pi.nf{opacity:.4}

/* PHONE */
.pbig{background:var(--bg2);border:1px solid var(--border);border-radius:10px;
  padding:20px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:14px}
.pstat{text-align:center}
.pv{font-size:24px;font-weight:800;margin-bottom:3px}
.pl{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.8px}
.pflag{font-size:44px}

/* RISK */
.rbar{height:5px;background:var(--bg3);border-radius:3px;overflow:hidden;margin-top:5px}
.rfill{height:100%;border-radius:3px;transition:width .5s}

/* STEALER */
.sti{background:var(--bg3);border:1px solid rgba(239,68,68,.2);
  border-radius:7px;padding:12px;margin-bottom:7px}
.sti:last-child{margin-bottom:0}

/* SEC HEADER ROW */
.shr{display:flex;justify-content:space-between;align-items:center;
  padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px}
.shr:last-child{border-bottom:none}

/* MAP */
.mapf{width:100%;height:270px;border:none;border-radius:8px}

/* RECENT */
.ri2{display:flex;align-items:center;gap:8px;padding:7px 0;
  border-bottom:1px solid rgba(255,255,255,.04);font-size:12px}
.ri2:last-child{border-bottom:none}
.rt2{margin-left:auto;color:var(--text3);font-size:11px}

/* EMPTY */
.empty{text-align:center;padding:32px;color:var(--text3)}
.empty i{font-size:28px;margin-bottom:10px;display:block;opacity:.25}

/* GLOW TOP */
body::before{content:'';position:fixed;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--accent),var(--cyan),var(--accent),transparent);
  opacity:.5;z-index:999;pointer-events:none}

/* FOOTER */
.footer{text-align:center;padding:12px;font-size:11px;color:var(--text3);
  border-top:1px solid var(--border);flex-shrink:0;background:var(--bg2)}

/* ═══════════ v0.0.3 NEON EDITION ═══════════ */
:root{
  --neon:#00ffc8;--neon2:#7c3aed;--neon3:#ff2fd6;
  --accent:#00e5ff;--accent2:#7c3aed;
}
html,body{background:#05060a}
body{background-image:radial-gradient(ellipse 60% 45% at 15% -5%,rgba(0,229,255,.10),transparent),radial-gradient(ellipse 55% 40% at 85% 0%,rgba(124,58,237,.14),transparent),radial-gradient(ellipse 50% 35% at 50% 110%,rgba(0,255,200,.07),transparent)}
body::before{height:2px;background:linear-gradient(90deg,transparent,#00e5ff,#7c3aed,#ff2fd6,#00ffc8,transparent);background-size:300% 100%;animation:neonFlow 6s linear infinite;opacity:.9;box-shadow:0 0 18px rgba(0,229,255,.55)}
@keyframes neonFlow{0%{background-position:0% 0}100%{background-position:300% 0}}
#nav{background:rgba(10,12,18,.92);backdrop-filter:blur(10px);border-bottom:1px solid rgba(0,229,255,.16);box-shadow:0 1px 24px rgba(0,229,255,.07)}
.nav-logo{font-size:17px;background:linear-gradient(90deg,#00e5ff,#7c3aed,#ff2fd6,#00e5ff);background-size:300% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:neonFlow 5s linear infinite;filter:drop-shadow(0 0 12px rgba(0,229,255,.45))}
.nl:hover{color:#fff;background:rgba(0,229,255,.07);border-color:rgba(0,229,255,.18)}
.nl.active{color:var(--neon);background:rgba(0,255,200,.07);border-color:rgba(0,255,200,.3);box-shadow:0 0 14px rgba(0,255,200,.18),inset 0 0 12px rgba(0,255,200,.05)}
.nbadge{background:rgba(0,255,200,.07);border:1px solid rgba(0,255,200,.35);color:var(--neon);box-shadow:0 0 12px rgba(0,255,200,.25);animation:neonPulse 2.6s ease-in-out infinite}
@keyframes neonPulse{0%,100%{box-shadow:0 0 8px rgba(0,255,200,.18)}50%{box-shadow:0 0 20px rgba(0,255,200,.45)}}
#body::-webkit-scrollbar{width:6px}
#body::-webkit-scrollbar-thumb{background:linear-gradient(180deg,var(--accent),var(--accent2));border-radius:3px;box-shadow:0 0 8px rgba(0,229,255,.4)}
.hero h1{background:linear-gradient(120deg,#fff 20%,#00e5ff 50%,#7c3aed 75%,#fff 95%);background-size:250% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:neonFlow 7s linear infinite;filter:drop-shadow(0 0 22px rgba(0,229,255,.25))}
.vbadges{display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap}
.vbadge{font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;border:1px solid rgba(0,229,255,.3);background:rgba(0,229,255,.06);color:var(--accent);box-shadow:0 0 10px rgba(0,229,255,.15)}
.vbadge.hot{border-color:rgba(255,47,214,.4);color:#ff7ae2;background:rgba(255,47,214,.06);box-shadow:0 0 10px rgba(255,47,214,.2)}
.searchbox{background:rgba(13,17,26,.9);border:1px solid rgba(0,229,255,.22);transition:all .25s}
.searchbox:focus-within{border-color:rgba(0,255,200,.55);box-shadow:0 0 24px rgba(0,255,200,.18)}
.stats{grid-template-columns:repeat(6,1fr)}
.stat-c{background:linear-gradient(160deg,rgba(20,26,40,.9),rgba(10,13,22,.9));border:1px solid rgba(0,229,255,.14);transition:all .2s}
.stat-c:hover{border-color:rgba(0,255,200,.4);box-shadow:0 0 18px rgba(0,255,200,.12);transform:translateY(-2px)}
.stat-n{text-shadow:0 0 16px currentColor}
.mcard{background:linear-gradient(165deg,rgba(20,26,40,.85),rgba(10,13,22,.9));border:1px solid rgba(0,229,255,.13)}
.mcard::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--accent),var(--neon3),transparent);opacity:0;transition:opacity .25s}
.mcard:hover{border-color:rgba(0,255,200,.45);transform:translateY(-3px);box-shadow:0 6px 28px rgba(0,255,200,.14)}
.mcard:hover::before{opacity:1}
.newtag{font-size:9px;font-weight:800;padding:2px 8px;border-radius:10px;background:linear-gradient(135deg,#ff2fd6,#7c3aed);color:#fff;letter-spacing:1px;box-shadow:0 0 12px rgba(255,47,214,.5);vertical-align:middle;margin-left:6px;animation:neonPulse 2s infinite}
.th{background:linear-gradient(165deg,rgba(20,26,40,.85),rgba(10,13,22,.9));border:1px solid rgba(0,229,255,.16)}
.rc{background:linear-gradient(165deg,rgba(18,23,36,.85),rgba(10,13,22,.92));border:1px solid rgba(0,229,255,.13)}
.rh{border-bottom:1px solid rgba(0,229,255,.12)}
.sc{background:linear-gradient(165deg,rgba(20,26,40,.9),rgba(10,13,22,.9));border:1px solid rgba(0,229,255,.14);transition:all .2s}
.sc:hover{border-color:rgba(0,255,200,.35);box-shadow:0 0 16px rgba(0,255,200,.12)}
.sn{text-shadow:0 0 18px currentColor}
.mi2{background:rgba(5,8,14,.8);border:1px solid rgba(0,229,255,.2)}
.mi2:focus{border-color:rgba(0,255,200,.6);box-shadow:0 0 14px rgba(0,255,200,.15)}
.msel{background:rgba(5,8,14,.9);border:1px solid rgba(0,229,255,.2)}
.mbtn{background:linear-gradient(135deg,#00c8ff,#7c3aed);box-shadow:0 0 16px rgba(0,200,255,.25);transition:all .2s}
.mbtn:hover{box-shadow:0 0 26px rgba(0,255,200,.45);transform:translateY(-1px)}
.mbtn.r{background:linear-gradient(135deg,#ff2f5f,#b91c1c);box-shadow:0 0 16px rgba(255,47,95,.3)}
.mbtn.ghost{background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.3);box-shadow:none;font-size:11px;padding:5px 12px}
.mbtn.ghost:hover{background:rgba(0,255,200,.12)}
.sec{color:var(--neon)}
.sec::after{background:linear-gradient(90deg,rgba(0,255,200,.35),transparent)}
.term{background:#030507;border:1px solid rgba(0,255,200,.25);box-shadow:inset 0 0 40px rgba(0,255,200,.03),0 0 20px rgba(0,255,200,.08);text-shadow:0 0 6px rgba(0,255,200,.25)}
.pi.found{border-color:rgba(34,197,94,.45);box-shadow:0 0 10px rgba(34,197,94,.12)}
.ldr-i{color:var(--neon)}
.spin{border:2px solid rgba(0,255,200,.15);border-top-color:var(--neon);box-shadow:0 0 10px rgba(0,255,200,.3)}
.pbig{background:linear-gradient(165deg,rgba(20,26,40,.85),rgba(10,13,22,.9));border:1px solid rgba(0,229,255,.16)}
#fab{position:fixed;right:22px;bottom:52px;width:52px;height:52px;border-radius:50%;border:1px solid rgba(0,255,200,.5);background:linear-gradient(135deg,#062a24,#0a1628);color:var(--neon);font-size:22px;cursor:pointer;z-index:500;box-shadow:0 0 22px rgba(0,255,200,.35);transition:all .2s}
#fab:hover{transform:scale(1.1) rotate(-8deg);box-shadow:0 0 34px rgba(0,255,200,.6)}
#toasts{position:fixed;right:22px;bottom:116px;display:flex;flex-direction:column;gap:8px;z-index:600;max-width:340px}
.toast{background:rgba(8,12,20,.95);border:1px solid var(--cyan);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--text);box-shadow:0 4px 24px rgba(0,0,0,.5);animation:toastIn .3s ease}
.toast.out{opacity:0;transform:translateX(30px);transition:all .4s}
@keyframes toastIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:none}}
.footer{background:rgba(8,10,16,.92);border-top:1px solid rgba(0,229,255,.14)}
.mt th{background:rgba(0,229,255,.05)}
.empty i{text-shadow:0 0 20px rgba(0,229,255,.3)}
@media(max-width:1200px){.stats{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:1fr}}
@media(max-width:700px){.stats{grid-template-columns:repeat(2,1fr)}.scards{grid-template-columns:1fr}.irow{flex-wrap:wrap}.pbig{grid-template-columns:1fr}}

</style>
</head>
<body>

<!-- NAV -->
<div id="nav">
  <div class="nav-logo">M-OSINT</div>
  <div class="nav-links">
    <div class="nl active" onclick="goPage('dash',this)"><i class="fas fa-home"></i>Dashboard</div>
    <div class="nl" onclick="goPage('breach',this)"><i class="fas fa-database"></i>Breach</div>
    <div class="nl" onclick="goPage('pass',this)"><i class="fas fa-key"></i>Şifre</div>
    <div class="nl" onclick="goPage('phone',this)"><i class="fas fa-phone"></i>Telefon</div>
    <div class="nl" onclick="goPage('user',this)"><i class="fas fa-user-secret"></i>Kullanıcı Adı</div>
    <div class="nl" onclick="goPage('ip',this)"><i class="fas fa-globe"></i>IP Sorgu</div>
    <div class="nl" onclick="goPage('dns',this)"><i class="fas fa-server"></i>DNS</div>
    <div class="nl" onclick="goPage('port',this)"><i class="fas fa-plug"></i>Port Tarama</div>
    <div class="nl" onclick="goPage('sub',this)"><i class="fas fa-sitemap"></i>Subdomain</div>
    <div class="nl" onclick="goPage('url',this)"><i class="fas fa-link"></i>URL Analiz</div>
    <div class="nl" onclick="goPage('email',this)"><i class="fas fa-envelope"></i>Email</div>
    <div class="nl" onclick="goPage('ssl',this)"><i class="fas fa-lock"></i>SSL</div>
    <div class="nl" onclick="goPage('hash',this)"><i class="fas fa-hashtag"></i>Hash</div>
    <div class="nl" onclick="goPage('crt',this)"><i class="fas fa-certificate"></i>CertIntel</div>
    <div class="nl" onclick="goPage('mac',this)"><i class="fas fa-network-wired"></i>MAC Vendor</div>
    <div class="nl" onclick="goPage('enc',this)"><i class="fas fa-code"></i>Encode/Decode</div>
    <div class="nl" onclick="goPage('tools',this)"><i class="fas fa-toolbox"></i>v0.0.5 Araçlar</div>
    <div class="nl" onclick="goPage('rt',this)"><i class="fas fa-satellite-dish"></i>Canlı</div>
  </div>
  <div class="nav-right">
    <div class="nbadge">""" + VERSION + """</div>
    <div class="nbadge2" id="clock">00:00:00</div>
  </div>
</div>

<div id="wrap">
<div id="body">

<!-- ═══════ DASHBOARD ═══════ -->
<div class="page active" id="page-dash">
  <div class="hero">
    <h1>M-OSINT Framework</h1>
    <p>Açık kaynak istihbarat aracı</p>
    <small>by """ + AUTHOR + """ — Sadece eğitim amaçlıdır</small>
    <div class="vbadges">
      <span class="vbadge hot">⚡ v0.0.5 Alpha — NEON</span>
      <span class="vbadge">👤 46 Platform</span>
      <span class="vbadge">🔒 SSL Analiz</span>
      <span class="vbadge">#️⃣ Hash Çözücü</span>
      <span class="vbadge">📜 CertIntel</span>
      <span class="vbadge">🔌 MAC Vendor</span>
      <span class="vbadge">🧩 Encode/Decode</span>
      <span class="vbadge">🧰 5 Yeni Araç</span>
    </div>
    <div class="searchbox">
      <input id="q-inp" placeholder="IP, domain, email, telefon veya kullanıcı adı...">
      <select id="q-type">
        <option value="breach">Breach</option>
        <option value="ip">IP</option>
        <option value="dns">DNS</option>
        <option value="email">Email</option>
        <option value="port">Port</option>
        <option value="phone">Telefon</option>
        <option value="username">Kullanıcı Adı</option>
        <option value="ssl">SSL</option>
        <option value="hash">Hash</option>
        <option value="crt">CertIntel</option>
      </select>
      <button onclick="quickScan()"><i class="fas fa-search"></i> Ara</button>
    </div>
    <div class="ldr" id="q-ldr"><div class="ldr-i"><span class="spin"></span>Sorgulanıyor...</div></div>
    <div id="q-res" style="max-width:620px;margin:10px auto 0;text-align:left"></div>
  </div>

  <div class="stats">
    <div class="stat-c">
      <div class="stat-ic" style="background:rgba(59,130,246,.1);color:var(--accent)">
        <i class="fas fa-search"></i></div>
      <div><div class="stat-n" id="s-total">0</div><div class="stat-l">Toplam</div></div>
    </div>
    <div class="stat-c">
      <div class="stat-ic" style="background:rgba(239,68,68,.1);color:var(--red)">
        <i class="fas fa-database"></i></div>
      <div><div class="stat-n" style="color:var(--red)" id="s-breach">0</div>
           <div class="stat-l">Breach</div></div>
    </div>
    <div class="stat-c">
      <div class="stat-ic" style="background:rgba(249,115,22,.1);color:var(--orange)">
        <i class="fas fa-bug"></i></div>
      <div><div class="stat-n" style="color:var(--orange)" id="s-stealer">0</div>
           <div class="stat-l">Stealer</div></div>
    </div>
    <div class="stat-c">
      <div class="stat-ic" style="background:rgba(34,197,94,.1);color:var(--green)">
        <i class="fas fa-plug"></i></div>
      <div><div class="stat-n" style="color:var(--green)" id="s-open">0</div>
           <div class="stat-l">Açık Port</div></div>
    </div>
    <div class="stat-c">
      <div class="stat-ic" style="background:rgba(168,85,247,.1);color:var(--purple)">
        <i class="fas fa-user"></i></div>
      <div><div class="stat-n" style="color:var(--purple)" id="s-user">0</div>
           <div class="stat-l">Profil</div></div>
    </div>
    <div class="stat-c">
      <div class="stat-ic" style="background:rgba(0,255,200,.08);color:var(--neon)">
        <i class="fas fa-lock"></i></div>
      <div><div class="stat-n" style="color:var(--neon)" id="s-cert">0</div>
           <div class="stat-l">SSL / Cert</div></div>
    </div>
  </div>

  <div class="sec"><i class="fas fa-th" style="color:var(--accent)"></i>Modüller</div>
  <div class="mgrid" style="margin-bottom:20px">
    <div class="mcard" onclick="goPage('breach',document.querySelectorAll('.nl')[1])">
      <div class="mi">🔓</div><div class="mn">Breach & Leak</div>
      <div class="md">3 kaynak paralel tarama</div>
    </div>
    <div class="mcard" onclick="goPage('pass',document.querySelectorAll('.nl')[2])">
      <div class="mi">🔑</div><div class="mn">Şifre Kontrolü</div>
      <div class="md">HIBP k-Anonymity</div>
    </div>
    <div class="mcard" onclick="goPage('phone',document.querySelectorAll('.nl')[3])">
      <div class="mi">📱</div><div class="mn">Telefon Sorgu</div>
      <div class="md">Ülke, operatör, risk</div>
    </div>
    <div class="mcard" onclick="goPage('user',document.querySelectorAll('.nl')[4])">
      <div class="mi">👤</div><div class="mn">Kullanıcı Adı</div>
      <div class="md">46 platform • akıllı tespit</div>
    </div>
    <div class="mcard" onclick="goPage('ip',document.querySelectorAll('.nl')[5])">
      <div class="mi">🌐</div><div class="mn">IP Sorgu</div>
      <div class="md">Konum, ISP, harita</div>
    </div>
    <div class="mcard" onclick="goPage('dns',document.querySelectorAll('.nl')[6])">
      <div class="mi">🖥️</div><div class="mn">DNS Sorgu</div>
      <div class="md">Kayıtlar + WHOIS</div>
    </div>
    <div class="mcard" onclick="goPage('port',document.querySelectorAll('.nl')[7])">
      <div class="mi">🔌</div><div class="mn">Port Tarama</div>
      <div class="md">TCP + Banner</div>
    </div>
    <div class="mcard" onclick="goPage('sub',document.querySelectorAll('.nl')[8])">
      <div class="mi">🗂️</div><div class="mn">Subdomain</div>
      <div class="md">60+ DNS tarama</div>
    </div>
    <div class="mcard" onclick="goPage('url',document.querySelectorAll('.nl')[9])">
      <div class="mi">🔗</div><div class="mn">URL Analiz</div>
      <div class="md">Teknoloji + güvenlik</div>
    </div>
    <div class="mcard" onclick="goPage('email',document.querySelectorAll('.nl')[10])">
      <div class="mi">📧</div><div class="mn">Email Analiz</div>
      <div class="md">MX + Gravatar</div>
    </div>
    <div class="mcard" onclick="goPage('ssl',document.querySelectorAll('.nl')[11])">
      <div class="mi">🔒</div><div class="mn">SSL Analiz <span class="newtag">YENİ</span></div>
      <div class="md">Sertifika + TLS notu</div>
    </div>
    <div class="mcard" onclick="goPage('hash',document.querySelectorAll('.nl')[12])">
      <div class="mi">#️⃣</div><div class="mn">Hash Çözücü <span class="newtag">YENİ</span></div>
      <div class="md">Tanımla + sözlük tara</div>
    </div>
    <div class="mcard" onclick="goPage('crt',document.querySelectorAll('.nl')[13])">
      <div class="mi">📜</div><div class="mn">CertIntel <span class="newtag">YENİ</span></div>
      <div class="md">crt.sh subdomain avı</div>
    </div>
  </div>

  <div class="sec"><i class="fas fa-history" style="color:var(--accent)"></i>Son Sorgular</div>
  <div class="rc"><div id="recent-list">
    <div class="empty"><i class="fas fa-clock"></i>Henüz sorgu yapılmadı</div>
  </div></div>
</div>

<!-- ═══════ BREACH ═══════ -->
<div class="page" id="page-breach">
  <div class="th">
    <h2><i class="fas fa-database" style="color:var(--red)"></i>Breach & Leak Tarama</h2>
    <p>LeakCheck.io + HudsonRock Cavalier + HIBP — 3 kaynak eş zamanlı</p>
    <div class="irow">
      <input class="mi2" id="br-inp" placeholder="hedef@domain.com">
      <button class="mbtn r" id="br-btn" onclick="doBreachFull()">
        <i class="fas fa-search"></i> Tara
      </button>
    </div>
  </div>
  <div class="ldr" id="br-ldr">
    <div class="ldr-i"><span class="spin"></span>3 kaynak taranıyor...</div>
  </div>
  <div id="br-res"></div>
</div>

<!-- ═══════ ŞİFRE ═══════ -->
<div class="page" id="page-pass">
  <div class="th">
    <h2><i class="fas fa-key" style="color:var(--yellow)"></i>Şifre Sızıntı Kontrolü</h2>
    <p>🔒 k-Anonymity — Şifreniz asla gönderilmez, sadece SHA1 hash'in ilk 5 karakteri kullanılır</p>
    <div class="irow">
      <input class="mi2" id="pw-inp" type="password" placeholder="Kontrol edilecek şifreyi girin...">
      <button class="mbtn" onclick="doPassword()">
        <i class="fas fa-shield-alt"></i> Kontrol Et
      </button>
    </div>
  </div>
  <div class="ldr" id="pw-ldr">
    <div class="ldr-i"><span class="spin"></span>Kontrol ediliyor...</div>
  </div>
  <div id="pw-res"></div>
</div>

<!-- ═══════ TELEFON ═══════ -->
<div class="page" id="page-phone">
  <div class="th">
    <h2><i class="fas fa-phone" style="color:var(--green)"></i>Telefon Numarası Sorgu</h2>
    <p>Ülke tespiti, operatör analizi, hat tipi ve risk skoru</p>
    <div class="irow">
      <input class="mi2" id="ph-inp" placeholder="+90 555 123 45 67">
      <button class="mbtn" onclick="doPhone()">
        <i class="fas fa-search"></i> Sorgula
      </button>
    </div>
  </div>
  <div class="ldr" id="ph-ldr">
    <div class="ldr-i"><span class="spin"></span>Analiz ediliyor...</div>
  </div>
  <div id="ph-res"></div>
</div>

<!-- ═══════ KULLANICI ADI ═══════ -->
<div class="page" id="page-user">
  <div class="th">
    <h2><i class="fas fa-user-secret" style="color:var(--purple)"></i>Kullanıcı Adı Tarama</h2>
    <p>46 sosyal medya ve platform üzerinde akıllı içerik doğrulamalı tarama</p>
    <div class="irow">
      <input class="mi2" id="un-inp" placeholder="kullaniciadi">
      <button class="mbtn" id="un-btn" onclick="doUsername()">
        <i class="fas fa-search"></i> Ara
      </button>
    </div>
  </div>
  <div class="ldr" id="un-ldr">
    <div class="ldr-i"><span class="spin"></span>46 platform taranıyor...</div>
  </div>
  <div id="un-res"></div>
</div>

<!-- ═══════ IP ═══════ -->
<div class="page" id="page-ip">
  <div class="th">
    <h2><i class="fas fa-globe" style="color:var(--cyan)"></i>IP Adres Sorgu</h2>
    <p>Konum, ISP, ASN, blacklist ve interaktif harita</p>
    <div class="irow">
      <input class="mi2" id="ip-inp" placeholder="8.8.8.8 veya domain.com">
      <button class="mbtn" onclick="doIP()">
        <i class="fas fa-search"></i> Sorgula
      </button>
    </div>
  </div>
  <div class="ldr" id="ip-ldr">
    <div class="ldr-i"><span class="spin"></span>Sorgulanıyor...</div>
  </div>
  <div id="ip-res"></div>
</div>

<!-- ═══════ DNS ═══════ -->
<div class="page" id="page-dns">
  <div class="th">
    <h2><i class="fas fa-server" style="color:var(--green)"></i>DNS Sorgu</h2>
    <p>A, AAAA, MX, NS, TXT, CNAME, SOA kayıtları ve WHOIS</p>
    <div class="irow">
      <input class="mi2" id="dns-inp" placeholder="ornek.com">
      <button class="mbtn" onclick="doDNS()">
        <i class="fas fa-search"></i> Sorgula
      </button>
    </div>
  </div>
  <div class="ldr" id="dns-ldr">
    <div class="ldr-i"><span class="spin"></span>Sorgulanıyor...</div>
  </div>
  <div id="dns-res"></div>
</div>

<!-- ═══════ PORT ═══════ -->
<div class="page" id="page-port">
  <div class="th">
    <h2><i class="fas fa-plug" style="color:var(--yellow)"></i>Port Tarama</h2>
    <p>TCP port tarama, servis tespiti ve banner grabbing</p>
    <div class="irow">
      <input class="mi2" id="pt-inp" placeholder="192.168.1.1 veya domain.com">
      <select class="msel" id="pt-rng">
        <option value="common">Yaygın Portlar</option>
        <option value="top100">İlk 100</option>
        <option value="top1000">İlk 1000</option>
      </select>
      <button class="mbtn" id="pt-btn" onclick="doPort()">
        <i class="fas fa-play"></i> Tara
      </button>
    </div>
  </div>
  <div class="ldr" id="pt-ldr">
    <div class="ldr-i"><span class="spin"></span>Taranıyor... Lütfen bekleyin</div>
  </div>
  <div id="pt-res"></div>
</div>

<!-- ═══════ SUBDOMAIN ═══════ -->
<div class="page" id="page-sub">
  <div class="th">
    <h2><i class="fas fa-sitemap" style="color:var(--accent)"></i>Subdomain Tarama</h2>
    <p>60+ yaygın subdomain DNS çözümlemesi ile taranır</p>
    <div class="irow">
      <input class="mi2" id="sd-inp" placeholder="ornek.com">
      <button class="mbtn" id="sd-btn" onclick="doSubdomain()">
        <i class="fas fa-play"></i> Tara
      </button>
    </div>
  </div>
  <div class="ldr" id="sd-ldr">
    <div class="ldr-i"><span class="spin"></span>Subdomainler taranıyor...</div>
  </div>
  <div id="sd-res"></div>
</div>

<!-- ═══════ URL ═══════ -->
<div class="page" id="page-url">
  <div class="th">
    <h2><i class="fas fa-link" style="color:var(--purple)"></i>URL / Domain Analiz</h2>
    <p>Teknoloji tespiti, güvenlik başlıkları, redirect zinciri</p>
    <div class="irow">
      <input class="mi2" id="url-inp" placeholder="https://ornek.com">
      <button class="mbtn" onclick="doURL()">
        <i class="fas fa-search"></i> Analiz Et
      </button>
    </div>
  </div>
  <div class="ldr" id="url-ldr">
    <div class="ldr-i"><span class="spin"></span>Analiz ediliyor...</div>
  </div>
  <div id="url-res"></div>
</div>

<!-- ═══════ EMAIL ═══════ -->
<div class="page" id="page-email">
  <div class="th">
    <h2><i class="fas fa-envelope" style="color:var(--purple)"></i>Email Analiz</h2>
    <p>Format, MX kayıtları, Gravatar ve sosyal medya tahmini</p>
    <div class="irow">
      <input class="mi2" id="em-inp" placeholder="hedef@domain.com">
      <button class="mbtn" onclick="doEmail()">
        <i class="fas fa-search"></i> Analiz Et
      </button>
    </div>
  </div>
  <div class="ldr" id="em-ldr">
    <div class="ldr-i"><span class="spin"></span>Analiz ediliyor...</div>
  </div>
  <div id="em-res"></div>
</div>

<!-- ═══════ SSL ═══════ -->
<div class="page" id="page-ssl">
  <div class="th">
    <h2><i class="fas fa-lock" style="color:var(--neon)"></i>SSL / TLS Sertifika Analizi <span class="newtag">YENİ</span></h2>
    <p>Sertifika zinciri, bitiş süresi, issuer, SAN listesi, TLS sürümü ve güvenlik notu</p>
    <div class="irow">
      <input class="mi2" id="ssl-inp" placeholder="ornek.com veya ornek.com:443">
      <button class="mbtn" id="ssl-btn" onclick="doSSL()">
        <i class="fas fa-shield-alt"></i> Analiz Et
      </button>
    </div>
  </div>
  <div class="ldr" id="ssl-ldr">
    <div class="ldr-i"><span class="spin"></span>Sertifika çekiliyor...</div>
  </div>
  <div id="ssl-res"></div>
</div>

<!-- ═══════ HASH ═══════ -->
<div class="page" id="page-hash">
  <div class="th">
    <h2><i class="fas fa-hashtag" style="color:var(--purple)"></i>Hash Analiz & Çözücü <span class="newtag">YENİ</span></h2>
    <p>Hash tipini tanımla, ücretsiz sözlüklerde ara — düz metin girersen hash'lerini üretir</p>
    <div class="irow">
      <input class="mi2" id="hash-inp" placeholder="5d41402abc4b2a76b9719d911017c592 veya düz metin...">
      <button class="mbtn" id="hash-btn" onclick="doHash()">
        <i class="fas fa-fingerprint"></i> Çözümle
      </button>
    </div>
  </div>
  <div class="ldr" id="hash-ldr">
    <div class="ldr-i"><span class="spin"></span>Analiz ediliyor...</div>
  </div>
  <div id="hash-res"></div>
</div>

<!-- ═══════ CERTINTEL ═══════ -->
<div class="page" id="page-crt">
  <div class="th">
    <h2><i class="fas fa-certificate" style="color:var(--cyan)"></i>CertIntel — Sertifika Şeffaflığı <span class="newtag">YENİ</span></h2>
    <p>crt.sh Certificate Transparency kayıtlarından gerçek subdomain keşfi</p>
    <div class="irow">
      <input class="mi2" id="crt-inp" placeholder="ornek.com">
      <button class="mbtn" id="crt-btn" onclick="doCRT()">
        <i class="fas fa-search"></i> Keşfet
      </button>
    </div>
  </div>
  <div class="ldr" id="crt-ldr">
    <div class="ldr-i"><span class="spin"></span>crt.sh taranıyor...</div>
  </div>
  <div id="crt-res"></div>
</div>

<!-- ═══════ MAC VENDOR ═══════ -->
<div class="page" id="page-mac">
  <div class="th">
    <h2><i class="fas fa-network-wired" style="color:var(--purple)"></i>MAC Adres Vendor Sorgusu <span class="newtag">YENİ</span></h2>
    <p>MAC adresinden üretici (OUI) tespiti + local/multicast bit analizi</p>
    <div class="irow">
      <input class="mi2" id="mac-inp" placeholder="AA:BB:CC:DD:EE:FF">
      <button class="mbtn" id="mac-btn" onclick="doMAC()">
        <i class="fas fa-search"></i> Sorgula
      </button>
    </div>
  </div>
  <div class="ldr" id="mac-ldr">
    <div class="ldr-i"><span class="spin"></span>Sorgulanıyor...</div>
  </div>
  <div id="mac-res"></div>
</div>

<!-- ═══════ ENCODE / DECODE ═══════ -->
<div class="page" id="page-enc">
  <div class="th">
    <h2><i class="fas fa-code" style="color:var(--cyan)"></i>Encode / Decode Aracı <span class="newtag">YENİ</span></h2>
    <p>Base64, URL, Hex ve ROT13 — çevrimdışı, tamamen lokal çalışır</p>
    <div class="irow">
      <select class="mi2" id="enc-mode" style="flex:0 0 200px">
        <option value="b64_encode">Base64 — Encode</option>
        <option value="b64_decode">Base64 — Decode</option>
        <option value="url_encode">URL — Encode</option>
        <option value="url_decode">URL — Decode</option>
        <option value="hex_encode">Hex — Encode</option>
        <option value="hex_decode">Hex — Decode</option>
        <option value="rot13">ROT13</option>
      </select>
      <input class="mi2" id="enc-inp" placeholder="Metin veya kod girin...">
      <button class="mbtn" id="enc-btn" onclick="doEncode()">
        <i class="fas fa-bolt"></i> Çevir
      </button>
    </div>
  </div>
  <div id="enc-res"></div>
</div>

<!-- ═══════ v0.0.5 ARAÇLAR ═══════ -->
<div class="page" id="page-tools">
  <div class="th">
    <h2><i class="fas fa-toolbox" style="color:var(--neon)"></i>v0.0.5 Araç Kutusu <span class="newtag">5 YENİ</span></h2>
    <p>E-posta kimlik doğrulama, web ayak izi, security.txt, IOC çıkarma ve yerel şifre gücü analizi.</p>
    <div class="irow">
      <select class="msel" id="tool-mode" onchange="setToolHint()">
        <option value="email-auth">E-posta güvenliği: SPF / DMARC / MX</option>
        <option value="footprint">Web ayak izi: robots.txt / sitemap</option>
        <option value="security-txt">security.txt denetimi</option>
        <option value="ioc-extract">IOC çıkarıcı: metinden IP / URL / hash</option>
        <option value="password-strength">Şifre gücü: yerel analiz</option>
      </select>
      <input class="mi2" id="tool-inp" placeholder="ornek.com">
      <button class="mbtn" id="tool-btn" onclick="doTool()"><i class="fas fa-play"></i> Çalıştır</button>
    </div>
    <small id="tool-hint" style="display:block;margin-top:10px;color:var(--text3)">Alan adı girin; SPF, DMARC ve MX kayıtları incelenecek.</small>
  </div>
  <div class="ldr" id="tool-ldr"><div class="ldr-i"><span class="spin"></span>Analiz ediliyor...</div></div>
  <div id="tool-res"></div>
</div>

<!-- ═══════ CANLI ═══════ -->
<div class="page" id="page-rt">
  <div class="th">
    <h2><i class="fas fa-satellite-dish" style="color:var(--orange)"></i>Gerçek Zamanlı Tarama</h2>
    <p>WebSocket ile anlık sonuçlar</p>
    <div class="irow">
      <input class="mi2" id="rt-inp" placeholder="Hedef girin...">
      <select class="msel" id="rt-type">
        <option value="ip">IP</option>
        <option value="port">Port</option>
        <option value="dns">DNS</option>
        <option value="email">Email</option>
        <option value="breach">Breach</option>
        <option value="phone">Telefon</option>
        <option value="username">Username</option>
        <option value="ssl">SSL</option>
        <option value="hash">Hash</option>
        <option value="crt">CertIntel</option>
        <option value="mac">MAC Vendor</option>
      </select>
      <button class="mbtn" id="rt-btn" onclick="startRT()">
        <i class="fas fa-play"></i> Başlat
      </button>
      <button class="mbtn r" id="rt-stop" onclick="stopRT()" style="display:none">
        <i class="fas fa-stop"></i> Durdur
      </button>
    </div>
  </div>
  <div class="term" id="rt-log">
    <span style="color:#374151">[ M-OSINT """ + VERSION + """ — Gerçek Zamanlı Terminal ]</span><br>
    <span style="color:#374151">[ by """ + AUTHOR + """ ]</span><br><br>
  </div>
  <div id="rt-res" style="margin-top:12px"></div>
</div>

</div><!-- /body -->

<div class="footer">
  M-OSINT """ + VERSION + """ &nbsp;·&nbsp; by <strong style="color:var(--accent)">""" + AUTHOR + """</strong>
  &nbsp;·&nbsp; ⚡ Neon Edition &nbsp;·&nbsp; Sadece eğitim amaçlıdır
</div>
</div><!-- /wrap -->

<div id="toasts"></div>
<button id="fab" onclick="dlLast()" title="Sonucu JSON indir">📥</button>

<script>
// ════════════════════════════════════════
// GLOBALS
// ════════════════════════════════════════
const socket = io();
let scanCount = 0;
let recentScans = [];
let stats = {total:0, breach:0, stealer:0, open:0, user:0, cert:0};

// ════════════════════════════════════════
// CLOCK
// ════════════════════════════════════════
setInterval(() => {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('tr-TR',
    {hour:'2-digit', minute:'2-digit', second:'2-digit'});
}, 1000);

// ════════════════════════════════════════
// PAGE NAV
// ════════════════════════════════════════
function goPage(name, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nl').forEach(n => n.classList.remove('active'));
  const pg = document.getElementById('page-' + name);
  if (pg) pg.classList.add('active');
  if (el && el.classList) el.classList.add('active');
}

// ════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════
function show(id) {
  const e = document.getElementById(id);
  if (e) e.style.display = 'block';
}
function hide(id) {
  const e = document.getElementById(id);
  if (e) e.style.display = 'none';
}
function setHTML(id, html) {
  const e = document.getElementById(id);
  if (e) e.innerHTML = html;
}

async function apiCall(ep, data) {
  try {
    const r = await fetch(ep, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const _j = await r.json();
    window._lastRes = _j; window._lastEp = ep;
    return _j;
  } catch(e) {
    return {error: e.message};
  }
}

function incStat(key, val=1) {
  if (key in stats) stats[key] += val;
  stats.total++;
  Object.keys(stats).forEach(k => {
    const el = document.getElementById('s-' + k);
    if (el) el.textContent = stats[k];
  });
  scanCount++;
}

function addRecent(type, target, cls='bb') {
  recentScans.unshift({type, target, cls,
    time: new Date().toLocaleTimeString('tr-TR')});
  if (recentScans.length > 10) recentScans.pop();
  const el = document.getElementById('recent-list');
  if (!el) return;
  el.innerHTML = recentScans.map(s => `
    <div class="ri2">
      <span class="b ${s.cls}">${s.type}</span>
      <span style="color:var(--text2);font-size:12px">${s.target}</span>
      <span class="rt2">${s.time}</span>
    </div>`).join('');
}

// ════════════════════════════════════════
// QUICK SCAN
// ════════════════════════════════════════
async function quickScan() {
  const inp  = document.getElementById('q-inp');
  const type = document.getElementById('q-type');
  if (!inp || !inp.value.trim()) return;
  const val = inp.value.trim();

  show('q-ldr');
  setHTML('q-res', '');

  const map = {
    breach:   ['/api/breach/full',  {email:    val}],
    ip:       ['/api/ip',           {ip:       val}],
    dns:      ['/api/dns',          {domain:   val}],
    email:    ['/api/email',        {email:    val}],
    port:     ['/api/port',         {host:     val, range:'common'}],
    phone:    ['/api/phone',        {phone:    val}],
    username: ['/api/username',     {username: val}],
    ssl:      ['/api/ssl',          {host:     val}],
    hash:     ['/api/hash',         {hash:     val}],
    crt:      ['/api/crt',          {domain:   val}],
  };
  const [ep, body] = map[type.value] || ['/api/ip', {ip: val}];
  const res = await apiCall(ep, body);

  hide('q-ldr');
  setHTML('q-res', `
    <div class="rc" style="margin-top:10px">
      <pre style="color:#22c55e;white-space:pre-wrap;font-size:11px;font-family:monospace">
${JSON.stringify(res, null, 2)}</pre>
    </div>`);
  incStat('total');
  addRecent(type.value.toUpperCase(), val, 'bb');
}

// ════════════════════════════════════════
// BREACH
// ════════════════════════════════════════
async function doBreachFull() {
  const el  = document.getElementById('br-inp');
  const btn = document.getElementById('br-btn');
  if (!el || !el.value.trim()) return;
  const email = el.value.trim();

  if (btn) btn.disabled = true;
  show('br-ldr');
  setHTML('br-res', '');

  const r   = await apiCall('/api/breach/full', {email});
  hide('br-ldr');
  if (btn) btn.disabled = false;

  if (r.error) {
    setHTML('br-res', `<div class="rc"><span class="b br">Hata: ${r.error}</span></div>`);
    return;
  }

  const sum = r.summary  || {};
  const lc  = r.leakcheck || {};
  const hr  = r.hudsonrock || {};
  const hb  = r.hibp      || {};

  if (sum.total_breaches > 0) incStat('breach', sum.total_breaches);
  if (hr.found) incStat('stealer', hr.stealer_count || 1);
  addRecent('BREACH', email, 'br');

  setHTML('br-res', `
    <div class="scards">
      <div class="sc">
        <div class="sn" style="color:${sum.total_breaches>0?'var(--red)':'var(--green)'}">
          ${sum.total_breaches || 0}</div>
        <div class="sl">Toplam Breach</div>
      </div>
      <div class="sc">
        <div class="sn" style="color:${hr.found?'var(--orange)':'var(--green)'}">
          ${hr.found ? hr.stealer_count : 'Temiz'}</div>
        <div class="sl">Infostealer</div>
      </div>
      <div class="sc">
        <div class="sn" style="color:var(--cyan)">${sum.sources_with_data||0}/3</div>
        <div class="sl">Kaynak</div>
      </div>
    </div>

    <div class="rc" style="margin-bottom:10px">
      <div class="rh">
        <span class="ri" style="color:${lc.found?'var(--red)':'var(--green)'}">
          <i class="fas fa-search"></i></span>
        <span class="rt" style="margin-left:6px">LeakCheck.io</span>
        <span class="rb">
          ${lc.found
            ? `<span class="b br">🚨 ${lc.breach_count} Breach</span>`
            : `<span class="b bg">✅ Temiz</span>`}
        </span>
      </div>
      ${lc.error ? `<div class="b by" style="margin-bottom:8px">⚠ ${lc.error}</div>` : ''}
      ${lc.fields && lc.fields.length ? `
        <div style="margin-bottom:10px">
          <span style="font-size:11px;color:var(--text3)">Sızan alanlar: </span>
          ${lc.fields.map(f => `<span class="b by" style="margin:2px">${f}</span>`).join('')}
        </div>` : ''}
      ${lc.breaches && lc.breaches.length ? `
        <table class="mt">
          <thead><tr><th>Site</th><th>Tarih</th></tr></thead>
          <tbody>${lc.breaches.map(b => `
            <tr>
              <td><strong style="color:var(--text)">${b.name}</strong></td>
              <td style="color:var(--text3)">${b.date || '?'}</td>
            </tr>`).join('')}
          </tbody>
        </table>` : ''}
    </div>

    <div class="rc" style="margin-bottom:10px">
      <div class="rh">
        <span class="ri" style="color:${hr.found?'var(--orange)':'var(--green)'}">
          <i class="fas fa-bug"></i></span>
        <span class="rt" style="margin-left:6px">HudsonRock — Infostealer</span>
        <span class="rb">
          ${hr.found
            ? `<span class="b bo">🦠 ${hr.stealer_count} Cihaz</span>`
            : `<span class="b bg">✅ Temiz</span>`}
        </span>
      </div>
      ${hr.error ? `<div class="b by">⚠ ${hr.error}</div>` : ''}
      ${hr.stealers && hr.stealers.length ? hr.stealers.map(s => `
        <div class="sti">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span class="b br">🦠 Enfekte</span>
            <span style="font-size:11px;color:var(--text3)">
              ${new Date(s.date_compromised).toLocaleString('tr-TR')}</span>
          </div>
          <table class="mt">
            <tr><td class="k">Bilgisayar</td><td>${s.computer_name}</td></tr>
            <tr><td class="k">OS</td><td>${s.operating_system}</td></tr>
            <tr><td class="k">Malware</td>
                <td style="color:var(--orange);font-size:11px;word-break:break-all">
                  ${s.malware_path}</td></tr>
            <tr><td class="k">Antivirüs</td>
                <td>${s.antiviruses && s.antiviruses.length
                  ? s.antiviruses.map(a => `<span class="b bc" style="margin:1px">${a}</span>`).join('')
                  : '<span class="b br">Yok</span>'}</td></tr>
            <tr><td class="k">Kurumsal</td>
                <td style="color:var(--cyan)">${(s.total_corporate||0).toLocaleString()}</td></tr>
          </table>
        </div>`).join('') : ''}
    </div>

    <div class="rc">
      <div class="rh">
        <span class="ri" style="color:${hb.found?'var(--red)':'var(--green)'}">
          <i class="fas fa-database"></i></span>
        <span class="rt" style="margin-left:6px">HIBP Public</span>
        <span class="rb">
          ${hb.found
            ? `<span class="b br">🚨 ${hb.breach_count} Eşleşme</span>`
            : `<span class="b bg">✅ Temiz</span>`}
        </span>
      </div>
      ${hb.error ? `<div class="b by">⚠ ${hb.error}</div>` : ''}
      <p style="font-size:11px;color:var(--text3);margin-bottom:8px">
        ${hb.total_in_db||0} breach veritabanında arandı</p>
      ${hb.breaches && hb.breaches.length ? `
        <table class="mt">
          <thead><tr><th>Breach</th><th>Tarih</th><th>Etkilenen</th><th>Veriler</th></tr></thead>
          <tbody>${hb.breaches.map(b => `
            <tr>
              <td><strong>${b.name}</strong></td>
              <td style="color:var(--text3)">${b.date}</td>
              <td style="color:var(--cyan)">${(b.count||0).toLocaleString()}</td>
              <td>${(b.data_types||[]).slice(0,4).map(d =>
                `<span class="b by" style="margin:1px;font-size:10px">${d}</span>`).join('')}</td>
            </tr>`).join('')}
          </tbody>
        </table>` : ''}
    </div>`);
}

// ════════════════════════════════════════
// PASSWORD
// ════════════════════════════════════════
async function doPassword() {
  const el = document.getElementById('pw-inp');
  if (!el || !el.value) return;
  const pw = el.value;

  show('pw-ldr');
  setHTML('pw-res', '');

  const r = await apiCall('/api/breach/password', {password: pw});
  hide('pw-ldr');

  if (r.error) {
    setHTML('pw-res',
      `<div class="rc"><span class="b by">⚠ ${r.error}</span></div>`);
    return;
  }

  if (r.pwned) {
    incStat('breach');
    setHTML('pw-res', `
      <div class="rc" style="text-align:center;padding:28px">
        <div style="font-size:52px;margin-bottom:14px">🚨</div>
        <div class="b br" style="font-size:16px;padding:8px 22px;display:inline-flex">
          ${r.count.toLocaleString()} kez sızdı!
        </div>
        <p style="color:var(--text3);font-size:13px;margin-top:14px">
          Bu şifreyi kullandığınız tüm hesaplarda hemen değiştirin.
        </p>
      </div>`);
  } else {
    setHTML('pw-res', `
      <div class="rc" style="text-align:center;padding:28px">
        <div style="font-size:52px;margin-bottom:14px">✅</div>
        <div class="b bg" style="font-size:14px;padding:8px 22px;display:inline-flex">
          Bu şifre sızıntı veritabanlarında görülmedi
        </div>
      </div>`);
  }
}

// ════════════════════════════════════════
// PHONE
// ════════════════════════════════════════
async function doPhone() {
  const el = document.getElementById('ph-inp');
  if (!el || !el.value.trim()) return;
  const phone = el.value.trim();

  show('ph-ldr');
  setHTML('ph-res', '');

  const r = await apiCall('/api/phone', {phone});
  hide('ph-ldr');
  incStat('total');
  addRecent('PHONE', phone, 'bg');

  if (r.error && !r.valid) {
    setHTML('ph-res',
      `<div class="rc"><span class="b br">⚠ ${r.error}</span></div>`);
    return;
  }

  const rc = r.risk_score < 30
    ? 'var(--green)' : r.risk_score < 60
    ? 'var(--yellow)' : 'var(--red)';

  setHTML('ph-res', `
    <div class="pbig">
      <div class="pstat">
        <div class="pflag">${r.country_flag || '🌍'}</div>
        <div class="pv" style="font-size:18px;margin-top:8px">${r.country || 'N/A'}</div>
        <div class="pl">Ülke</div>
      </div>
      <div class="pstat">
        <div class="pv" style="color:var(--cyan)">${r.carrier || 'N/A'}</div>
        <div class="pl">Operatör</div>
      </div>
      <div class="pstat">
        <div class="pv" style="color:var(--yellow)">${r.line_type || 'N/A'}</div>
        <div class="pl">Hat Tipi</div>
      </div>
    </div>
    <div class="g2">
      <div class="rc">
        <div class="rh">
          <i class="fas fa-phone ri" style="color:var(--green)"></i>
          <span class="rt" style="margin-left:6px">Detaylar</span>
        </div>
        <table class="mt">
          <tr><td class="k">Girilen</td><td>${r.phone}</td></tr>
          <tr><td class="k">Uluslararası</td>
              <td style="color:var(--cyan);font-weight:600">
                ${r.formatted_international || 'N/A'}</td></tr>
          <tr><td class="k">Yerel Format</td>
              <td style="color:var(--cyan)">${r.formatted_local || 'N/A'}</td></tr>
          <tr><td class="k">Ülke</td>
              <td>${r.country_flag || ''} ${r.country || 'N/A'}</td></tr>
          <tr><td class="k">ISO</td>
              <td><span class="b bb">${r.country_iso || 'N/A'}</span></td></tr>
          <tr><td class="k">Alan Kodu</td>
              <td style="color:var(--yellow)">${r.country_dial || 'N/A'}</td></tr>
          <tr><td class="k">Yerel No</td><td>${r.local_number || 'N/A'}</td></tr>
          <tr><td class="k">Operatör</td>
              <td style="color:var(--green);font-weight:600">
                ${r.carrier || 'N/A'}</td></tr>
          <tr><td class="k">Hat Tipi</td><td>${r.line_type || 'N/A'}</td></tr>
        </table>
      </div>
      <div class="rc">
        <div class="rh">
          <i class="fas fa-shield-alt ri" style="color:${rc}"></i>
          <span class="rt" style="margin-left:6px">Risk Analizi</span>
          <span class="rb">
            <span class="b ${r.risk_score<30?'bg':r.risk_score<60?'by':'br'}">
              ${r.risk_score || 0}/100
            </span>
          </span>
        </div>
        <div style="margin-bottom:16px">
          <div style="display:flex;justify-content:space-between;
                      font-size:12px;margin-bottom:5px">
            <span style="color:var(--text3)">Risk Skoru</span>
            <span style="color:${rc};font-weight:700">${r.risk_score || 0}%</span>
          </div>
          <div class="rbar">
            <div class="rfill" style="width:${r.risk_score||0}%;background:${rc}"></div>
          </div>
        </div>
        ${r.tags && r.tags.length ? `
          <div style="margin-bottom:14px">
            ${r.tags.map(t =>
              `<span class="b bo" style="margin:2px">${t}</span>`).join('')}
          </div>` : ''}
        <div style="display:flex;flex-direction:column;gap:8px">
          ${r.whatsapp_link ? `
            <a href="${r.whatsapp_link}" target="_blank"
               style="display:flex;align-items:center;gap:8px;padding:10px 14px;
                      background:#075e54;border-radius:8px;color:#fff;
                      text-decoration:none;font-size:13px;font-weight:600">
              <i class="fab fa-whatsapp" style="font-size:16px"></i>
              WhatsApp'ta Aç
            </a>` : ''}
          ${r.telegram_link ? `
            <a href="${r.telegram_link}" target="_blank"
               style="display:flex;align-items:center;gap:8px;padding:10px 14px;
                      background:#0088cc;border-radius:8px;color:#fff;
                      text-decoration:none;font-size:13px;font-weight:600">
              <i class="fab fa-telegram" style="font-size:16px"></i>
              Telegram'da Aç
            </a>` : ''}
        </div>
      </div>
    </div>`);
}

// ════════════════════════════════════════
// USERNAME
// ════════════════════════════════════════
async function doUsername() {
  const el  = document.getElementById('un-inp');
  const btn = document.getElementById('un-btn');
  if (!el || !el.value.trim()) return;
  const username = el.value.trim();

  if (btn) btn.disabled = true;
  show('un-ldr');
  setHTML('un-res', '');

  const r = await apiCall('/api/username', {username});
  hide('un-ldr');
  if (btn) btn.disabled = false;
  window._lastRes = r; window._lastEp = '/api/username';
  incStat('user', r.total_found || 0);
  addRecent('USER', username, 'bp');
  toast(`Kullanıcı taraması: ${r.total_found||0}/${r.total_checked||0} bulundu`, (r.total_found>0?'ok':'info'));

  setHTML('un-res', `
    <div class="scards">
      <div class="sc">
        <div class="sn" style="color:var(--green)">${r.total_found || 0}</div>
        <div class="sl">Bulundu</div>
      </div>
      <div class="sc">
        <div class="sn" style="color:var(--text3)">${r.not_found?.length || 0}</div>
        <div class="sl">Bulunamadı</div>
      </div>
      <div class="sc">
        <div class="sn">${r.total_checked || 0}</div>
        <div class="sl">Taranan</div>
      </div>
    </div>
    ${(r.blocked && r.blocked.length) ? `<div class="rc" style="margin-bottom:10px;border-color:rgba(234,179,8,.35)"><div style="font-size:12px;color:var(--yellow)">⚠ ${r.blocked.length} platform bot koruması nedeniyle doğrulanamadı (manuel kontrol önerilir): <span style="color:var(--text2)">${(r.blocked||[]).map(b=>b.platform).join(', ')}</span></div></div>` : ''}
    <div class="rc" style="margin-bottom:10px">
      <div class="rh">
        <i class="fas fa-check-circle ri" style="color:var(--green)"></i>
        <span class="rt" style="margin-left:6px">
          Bulunan Profiller (${r.total_found || 0})
        </span>
      </div>
      <div class="pgrid">
        ${(r.found || []).map(p => `
          <div class="pi found">
            <span class="b bg" style="font-size:10px">✓</span>
            <a href="${p.url}" target="_blank">${p.platform}</a>
          </div>`).join('')
        || '<div class="empty"><i class="fas fa-times"></i>Profil bulunamadı</div>'}
      </div>
    </div>
    <div class="rc">
      <div class="rh">
        <i class="fas fa-times-circle ri" style="color:var(--text3)"></i>
        <span class="rt" style="margin-left:6px">Bulunamayan Platformlar</span>
      </div>
      <div class="pgrid">
        ${(r.not_found || []).map(p => `
          <div class="pi nf">
            <span class="b bgr" style="font-size:10px">✗</span>
            <span style="color:var(--text3)">${p.platform}</span>
          </div>`).join('')}
      </div>
    </div>`);
}

// ════════════════════════════════════════
// IP
// ════════════════════════════════════════
async function doIP() {
  const el = document.getElementById('ip-inp');
  if (!el || !el.value.trim()) return;
  const ip = el.value.trim();

  show('ip-ldr');
  setHTML('ip-res', '');

  const r = await apiCall('/api/ip', {ip});
  hide('ip-ldr');
  incStat('total');
  addRecent('IP', ip, 'bc');

  const info = r.info || {};
  setHTML('ip-res', `
    <div class="scards">
      <div class="sc">
        <div class="sn" style="font-size:20px">${info.country || 'N/A'}</div>
        <div class="sl">Ülke</div>
      </div>
      <div class="sc">
        <div class="sn" style="font-size:20px">${info.city || 'N/A'}</div>
        <div class="sl">Şehir</div>
      </div>
      <div class="sc">
        <div class="sn" style="font-size:14px">${r.asn?.asn || 'N/A'}</div>
        <div class="sl">ASN</div>
      </div>
    </div>
    <div class="g2">
      <div class="rc">
        <div class="rh">
          <i class="fas fa-info-circle ri" style="color:var(--cyan)"></i>
          <span class="rt" style="margin-left:6px">Bilgiler</span>
        </div>
        <table class="mt">
          ${[['IP',info.ip],['Hostname',info.hostname],['Şehir',info.city],
             ['Bölge',info.region],['Ülke',info.country],['ISP',info.isp],
             ['Org',info.org],['Koordinat',info.location],
             ['Timezone',info.timezone]
            ].map(([k,v]) => `
            <tr>
              <td class="k">${k}</td>
              <td style="color:var(--cyan)">${v || 'N/A'}</td>
            </tr>`).join('')}
        </table>
        ${r.map_link ? `
          <div style="display:flex;gap:7px;margin-top:12px">
            <a href="${r.map_link}" target="_blank" class="mbtn"
               style="font-size:11px;padding:6px 12px;text-decoration:none">
              🗺 OpenStreetMap
            </a>
            <a href="${r.google_maps}" target="_blank" class="mbtn"
               style="font-size:11px;padding:6px 12px;text-decoration:none;
                      background:linear-gradient(135deg,#1a73e8,#1558b0)">
              📍 Google Maps
            </a>
          </div>` : ''}
      </div>
      <div class="rc">
        <div class="rh">
          <i class="fas fa-ban ri" style="color:var(--red)"></i>
          <span class="rt" style="margin-left:6px">Blacklist</span>
        </div>
        ${Object.entries(r.blacklist || {}).map(([l, s]) => `
          <div class="shr">
            <span style="color:var(--text3);font-size:11px">${l}</span>
            <span class="b ${s===false?'bg':s===true?'br':'by'}">
              ${s===false?'✅ Temiz':s===true?'🚨 Listede':'⚠ Hata'}
            </span>
          </div>`).join('')}
        ${r.asn?.org ? `
          <div style="margin-top:12px;padding-top:10px;
                      border-top:1px solid var(--border)">
            <div style="font-size:11px;color:var(--text3);margin-bottom:3px">ASN Org</div>
            <div style="font-size:13px">${r.asn.org}</div>
          </div>` : ''}
      </div>
    </div>
    ${r.map_link && info.lat && info.lon ? `
    <div class="rc" style="margin-top:12px">
      <div class="rh">
        <i class="fas fa-map ri" style="color:var(--cyan)"></i>
        <span class="rt" style="margin-left:6px">Konum Haritası</span>
      </div>
      <iframe class="mapf"
        src="https://www.openstreetmap.org/export/embed.html?bbox=${parseFloat(info.lon)-0.05},${parseFloat(info.lat)-0.05},${parseFloat(info.lon)+0.05},${parseFloat(info.lat)+0.05}&layer=mapnik&marker=${info.lat},${info.lon}">
      </iframe>
    </div>` : ''}`);
}

// ════════════════════════════════════════
// DNS
// ════════════════════════════════════════
async function doDNS() {
  const el = document.getElementById('dns-inp');
  if (!el || !el.value.trim()) return;
  const domain = el.value.trim();

  show('dns-ldr');
  setHTML('dns-res', '');

  const r = await apiCall('/api/dns', {domain});
  hide('dns-ldr');
  incStat('total');
  addRecent('DNS', domain, 'bg');

  const w = r.whois || {};
  setHTML('dns-res', `
    <div class="g2">
      <div class="rc">
        <div class="rh">
          <i class="fas fa-list ri" style="color:var(--green)"></i>
          <span class="rt" style="margin-left:6px">DNS Kayıtları</span>
        </div>
        <table class="mt">
          <thead><tr><th>Tip</th><th>Değer</th></tr></thead>
          <tbody>
            ${Object.entries(r.records || {}).map(([type, vals]) =>
              (vals || []).filter(v => v).map(v => `
                <tr>
                  <td><span class="b bb">${type}</span></td>
                  <td style="font-size:11px;word-break:break-all;
                             color:var(--text2)">${v}</td>
                </tr>`).join('')
            ).join('')}
          </tbody>
        </table>
      </div>
      <div class="rc">
        <div class="rh">
          <i class="fas fa-id-card ri" style="color:var(--purple)"></i>
          <span class="rt" style="margin-left:6px">WHOIS</span>
        </div>
        <table class="mt">
          ${[['Registrar',w.registrar],['Kayıt',w.creation_date],
             ['Bitiş',w.expiration_date],['Ülke',w.country],
             ['Email', Array.isArray(w.emails)?w.emails.join(', '):w.emails]
            ].map(([k,v]) => `
            <tr>
              <td class="k">${k}</td>
              <td style="font-size:11px;color:var(--text2)">${v || 'N/A'}</td>
            </tr>`).join('')}
        </table>
        ${(w.name_servers || []).length ? `
          <div style="margin-top:10px;padding-top:8px;
                      border-top:1px solid var(--border)">
            <div style="font-size:11px;color:var(--text3);margin-bottom:5px">NS</div>
            ${w.name_servers.map(ns => `
              <div style="font-size:12px;color:var(--cyan);padding:2px 0">${ns}</div>
            `).join('')}
          </div>` : ''}
      </div>
    </div>`);
}

// ════════════════════════════════════════
// PORT
// ════════════════════════════════════════
async function doPort() {
  const el  = document.getElementById('pt-inp');
  const rng = document.getElementById('pt-rng');
  const btn = document.getElementById('pt-btn');
  if (!el || !el.value.trim()) return;
  const host = el.value.trim();

  if (btn) btn.disabled = true;
  show('pt-ldr');
  setHTML('pt-res', '');

  const r = await apiCall('/api/port', {host, range: rng ? rng.value : 'common'});
  hide('pt-ldr');
  if (btn) btn.disabled = false;

  if (r.open_ports?.length) incStat('open', r.open_ports.length);
  addRecent('PORT', host, 'by');

  setHTML('pt-res', `
    <div class="scards">
      <div class="sc">
        <div class="sn" style="color:var(--green)">${r.open_ports?.length || 0}</div>
        <div class="sl">Açık Port</div>
      </div>
      <div class="sc">
        <div class="sn" style="color:var(--red)">${r.closed_count || 0}</div>
        <div class="sl">Kapalı Port</div>
      </div>
      <div class="sc">
        <div class="sn" style="font-size:14px">${r.scan_time || 'N/A'}</div>
        <div class="sl">Tarama Süresi</div>
      </div>
    </div>
    <div class="rc">
      <div class="rh">
        <i class="fas fa-door-open ri" style="color:var(--green)"></i>
        <span class="rt" style="margin-left:6px">Açık Portlar</span>
      </div>
      ${!r.open_ports || !r.open_ports.length
        ? '<div class="empty"><i class="fas fa-lock"></i>Açık port bulunamadı</div>'
        : `<table class="mt">
            <thead>
              <tr><th>Port</th><th>Servis</th><th>Durum</th><th>Banner</th></tr>
            </thead>
            <tbody>
              ${r.open_ports.map(p => `
                <tr>
                  <td><strong style="color:var(--yellow)">${p.port}</strong></td>
                  <td><span class="b bb">${p.service}</span></td>
                  <td><span class="b bg">AÇIK</span></td>
                  <td style="font-size:10px;color:var(--text3)">${p.banner || '—'}</td>
                </tr>`).join('')}
            </tbody>
          </table>`}
    </div>`);
}

// ════════════════════════════════════════
// SUBDOMAIN
// ════════════════════════════════════════
async function doSubdomain() {
  const el  = document.getElementById('sd-inp');
  const btn = document.getElementById('sd-btn');
  if (!el || !el.value.trim()) return;
  const domain = el.value.trim();

  if (btn) btn.disabled = true;
  show('sd-ldr');
  setHTML('sd-res', '');

  const r = await apiCall('/api/subdomain', {domain});
  hide('sd-ldr');
  if (btn) btn.disabled = false;
  incStat('total');
  addRecent('SUB', domain, 'bb');

  setHTML('sd-res', `
    <div class="scards">
      <div class="sc">
        <div class="sn" style="color:var(--green)">${r.found?.length || 0}</div>
        <div class="sl">Bulundu</div>
      </div>
      <div class="sc">
        <div class="sn" style="color:var(--text3)">${r.not_found || 0}</div>
        <div class="sl">Bulunamadı</div>
      </div>
      <div class="sc">
        <div class="sn" style="font-size:14px">${r.scan_time || 'N/A'}</div>
        <div class="sl">Süre</div>
      </div>
    </div>
    <div class="rc">
      <div class="rh">
        <i class="fas fa-sitemap ri" style="color:var(--accent)"></i>
        <span class="rt" style="margin-left:6px">
          Bulunan Subdomainler (${r.found?.length || 0})
        </span>
      </div>
      ${!r.found || !r.found.length
        ? '<div class="empty"><i class="fas fa-times"></i>Subdomain bulunamadı</div>'
        : `<table class="mt">
            <thead><tr><th>Subdomain</th><th>IP</th><th>CNAME</th></tr></thead>
            <tbody>
              ${r.found.map(s => `
                <tr>
                  <td>
                    <a href="https://${s.subdomain}" target="_blank"
                       style="color:var(--cyan);text-decoration:none;font-weight:600">
                      ${s.subdomain}
                    </a>
                  </td>
                  <td><span class="b bg">${s.ip}</span></td>
                  <td style="color:var(--text3);font-size:11px">${s.cname || '—'}</td>
                </tr>`).join('')}
            </tbody>
          </table>`}
    </div>`);
}

// ════════════════════════════════════════
// URL
// ════════════════════════════════════════
async function doURL() {
  const el = document.getElementById('url-inp');
  if (!el || !el.value.trim()) return;
  const url = el.value.trim();

  show('url-ldr');
  setHTML('url-res', '');

  const r = await apiCall('/api/url', {url});
  hide('url-ldr');
  incStat('total');
  addRecent('URL', url, 'bp');

  const sh = r.security_headers || {};
  setHTML('url-res', `
    <div class="g2">
      <div class="rc">
        <div class="rh">
          <i class="fas fa-info-circle ri" style="color:var(--purple)"></i>
          <span class="rt" style="margin-left:6px">Genel</span>
          <span class="rb">
            <span class="b ${r.status_code==200?'bg':r.status_code>=400?'br':'by'}">
              HTTP ${r.status_code || '?'}
            </span>
          </span>
        </div>
        <table class="mt">
          <tr><td class="k">Final URL</td>
              <td><a href="${r.final_url}" target="_blank"
                     style="color:var(--cyan);font-size:11px;word-break:break-all">
                ${r.final_url}
              </a></td></tr>
          <tr><td class="k">Başlık</td><td>${r.title || 'N/A'}</td></tr>
          <tr><td class="k">Server</td>
              <td><span class="b bgr">${r.server || 'N/A'}</span></td></tr>
          <tr><td class="k">X-Powered-By</td>
              <td><span class="b bgr">${r.powered_by || 'N/A'}</span></td></tr>
          <tr><td class="k">IP</td>
              <td style="color:var(--cyan)">${r.ip || 'N/A'}</td></tr>
          <tr><td class="k">Redirect</td>
              <td><span class="b bo">${r.redirect_chain?.length || 0}</span></td></tr>
          <tr><td class="k">Güvenlik Skoru</td>
              <td><span class="b ${r.security_score>=80?'bg':r.security_score>=55?'by':'br'}">${r.security_score ?? '?'} / 100 (${r.risk_level||'?'})</span></td></tr>
        </table>
        ${r.technologies && r.technologies.length ? `
          <div style="margin-top:10px;padding-top:10px;
                      border-top:1px solid var(--border)">
            <div style="font-size:11px;color:var(--text3);margin-bottom:5px">
              Teknolojiler</div>
            ${r.technologies.map(t =>
              `<span class="b bc" style="margin:2px">${t}</span>`).join('')}
          </div>` : ''}
      </div>
      <div class="rc">
        <div class="rh">
          <i class="fas fa-shield-alt ri" style="color:var(--green)"></i>
          <span class="rt" style="margin-left:6px">Güvenlik Başlıkları</span>
        </div>
        ${Object.entries(sh).map(([h, v]) => `
          <div class="shr">
            <span style="font-size:11px;color:var(--text3)">${h}</span>
            <span class="b ${v ? 'bg' : 'br'}">${v ? '✅ Var' : '❌ Eksik'}</span>
          </div>`).join('')}
      </div>
    </div>`);
}

// ════════════════════════════════════════
// EMAIL
// ════════════════════════════════════════
async function doEmail() {
  const el = document.getElementById('em-inp');
  if (!el || !el.value.trim()) return;
  const email = el.value.trim();

  show('em-ldr');
  setHTML('em-res', '');

  const r = await apiCall('/api/email', {email});
  hide('em-ldr');
  incStat('total');
  addRecent('EMAIL', email, 'bp');

  const b = (v, t) => v
    ? `<span class="b bg">✅ ${t}</span>`
    : `<span class="b br">✗ ${t}</span>`;

  setHTML('em-res', `
    <div class="g2">
      <div class="rc">
        <div class="rh">
          <i class="fas fa-check-circle ri" style="color:var(--green)"></i>
          <span class="rt" style="margin-left:6px">Doğrulama</span>
        </div>
        <table class="mt">
          <tr><td class="k">Format</td><td>${b(r.format_valid,'Geçerli')}</td></tr>
          <tr><td class="k">Domain</td><td>${b(r.domain_valid,'Aktif')}</td></tr>
          <tr><td class="k">Geçici</td><td>${b(!r.disposable,'Hayır')}</td></tr>
          <tr><td class="k">Sağlayıcı</td>
              <td>${r.free_provider
                ? '<span class="b by">Ücretsiz</span>'
                : '<span class="b bb">Kurumsal</span>'}</td></tr>
          <tr><td class="k">Gravatar</td><td>${b(r.gravatar?.exists,'Mevcut')}</td></tr>
        </table>
        ${r.gravatar?.exists ? `
          <div style="margin-top:10px">
            <a href="${r.gravatar.url}" target="_blank"
               style="color:var(--cyan);font-size:12px">→ Gravatar Profili</a>
          </div>` : ''}
      </div>
      <div class="rc">
        <div class="rh">
          <i class="fas fa-server ri" style="color:var(--green)"></i>
          <span class="rt" style="margin-left:6px">MX & Sosyal</span>
        </div>
        ${(r.mx_records || []).map(m => `
          <div style="padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);
                      font-size:12px;color:var(--cyan)">${m}</div>
        `).join('') || '<span style="color:var(--text3);font-size:12px">MX bulunamadı</span>'}
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border)">
          <div style="font-size:11px;color:var(--text3);margin-bottom:6px">
            Sosyal Medya Tahmini</div>
          ${Object.entries(r.social_guess || {}).map(([k, v]) => `
            <div style="padding:3px 0;font-size:12px;display:flex;
                        align-items:center;gap:8px">
              <span class="b bgr" style="width:72px;justify-content:center">
                ${k}</span>
              <a href="${v}" target="_blank"
                 style="color:var(--cyan);text-decoration:none;font-size:11px">
                ${v}
              </a>
            </div>`).join('')}
        </div>
      </div>
    </div>`);
}

// ════════════════════════════════════════
// v0.0.3 — TOAST + RAPOR
// ════════════════════════════════════════
function toast(msg, type='info') {
  const box = document.getElementById('toasts');
  if (!box) return;
  const col = type==='ok' ? 'var(--green)' : type==='err' ? 'var(--red)' : 'var(--cyan)';
  const d = document.createElement('div');
  d.className = 'toast';
  d.style.borderColor = col;
  d.innerHTML = `<span style="color:${col}">●</span> <span>${msg}</span>`;
  box.appendChild(d);
  setTimeout(()=>{ d.classList.add('out'); setTimeout(()=>d.remove(), 400); }, 3200);
}
function dlLast() {
  if (!window._lastRes) { toast('İndirilecek sonuç yok — önce bir tarama yap', 'err'); return; }
  const blob = new Blob([JSON.stringify({exported_at: new Date().toISOString(), endpoint: window._lastEp||'?', data: window._lastRes}, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `mosint-${(window._lastEp||'sonuc').replace('/api/','')}-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  toast('Rapor indirildi 📥', 'ok');
}

// ════════════════════════════════════════
// SSL
// ════════════════════════════════════════
async function doSSL() {
  const el = document.getElementById('ssl-inp');
  if (!el || !el.value.trim()) return;
  const host = el.value.trim();
  show('ssl-ldr');
  setHTML('ssl-res', '');
  const r = await apiCall('/api/ssl', {host});
  hide('ssl-ldr');
  incStat('cert');
  addRecent('SSL', host, 'bg');
  if (r.error && !r.reachable) {
    setHTML('ssl-res', `<div class="rc"><span class="b br">⚠ ${r.error}</span></div>`);
    toast('SSL hatası: ' + r.error, 'err');
    return;
  }
  const gcol = (r.grade==='A+'||r.grade==='A') ? 'var(--green)' : r.grade==='B' ? 'var(--cyan)' : r.grade==='C' ? 'var(--yellow)' : 'var(--red)';
  const ck = r.checks || {}, cert = r.cert || {};
  const iss = cert.issuer || {};
  setHTML('ssl-res', `
    <div class="scards">
      <div class="sc"><div class="sn" style="color:${gcol};text-shadow:0 0 18px ${gcol}">${r.grade||'?'}</div><div class="sl">Güvenlik Notu</div></div>
      <div class="sc"><div class="sn" style="color:var(--cyan)">${cert.days_left ?? '?'}</div><div class="sl">Kalan Gün</div></div>
      <div class="sc"><div class="sn" style="font-size:14px">${r.tls_version||'N/A'}</div><div class="sl">TLS Sürümü</div></div>
    </div>
    <div class="g2">
      <div class="rc">
        <div class="rh"><i class="fas fa-certificate ri" style="color:var(--neon)"></i><span class="rt" style="margin-left:6px">Sertifika</span><span class="rb"><button class="mbtn ghost" onclick="dlLast()">📥 JSON</button></span></div>
        <table class="mt">
          ${[['Host',r.hostname],['IP',r.ip],['CN',(cert.common_name||'N/A')],['Issuer',(iss.organization||iss.commonName||'N/A')],['Seri',cert.serial],['Başlangıç',cert.not_before],['Bitiş',cert.not_after],['Cipher',(r.cipher||'N/A')]].map(([k,v])=>`<tr><td class="k">${k}</td><td style="color:var(--cyan);font-size:11px;word-break:break-all">${v||'N/A'}</td></tr>`).join('')}
        </table>
      </div>
      <div class="rc">
        <div class="rh"><i class="fas fa-check-double ri" style="color:var(--green)"></i><span class="rt" style="margin-left:6px">Kontroller</span></div>
        ${[['Süresi dolmuş',ck.expired,true],['Self-signed',ck.self_signed,true],['Hostname eşleşiyor',ck.hostname_match,false],['TLS 1.2/1.3',ck.tls_ok,false]].map(([k,v,inv])=>{const ok = inv ? !v : !!v; return `<div class="shr"><span style="font-size:12px;color:var(--text2)">${k}</span><span class="b ${ok?'bg':'br'}">${ok?'✅':'❌'}</span></div>`;}).join('')}
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border)">
          <div style="font-size:11px;color:var(--text3);margin-bottom:6px">SAN (${cert.san_count||0})</div>
          <div style="max-height:150px;overflow-y:auto">${((cert.sans||[]).map(x=>`<div style="font-size:11px;color:var(--cyan);padding:2px 0">${x}</div>`).join('')||'<span style="color:var(--text3)">—</span>')}</div>
        </div>
      </div>
    </div>`);
  toast('SSL analizi tamamlandı: ' + (r.grade||'?'), 'ok');
}

// ════════════════════════════════════════
// HASH
// ════════════════════════════════════════
async function doHash() {
  const el = document.getElementById('hash-inp');
  if (!el || !el.value.trim()) return;
  const hv = el.value.trim();
  show('hash-ldr');
  setHTML('hash-res', '');
  const r = await apiCall('/api/hash', {hash: hv});
  hide('hash-ldr');
  incStat('total');
  addRecent('HASH', hv.slice(0, 24), 'by');
  if (r.error && !r.input) {
    setHTML('hash-res', `<div class="rc"><span class="b br">⚠ ${r.error}</span></div>`);
    return;
  }
  const types = (r.possible_types||[]).map(t=>`<span class="b bp" style="margin:2px">${t}</span>`).join('');
  let lookupHtml = '';
  if (r.is_hash) {
    if (r.lookup && r.lookup.found && r.lookup.plain) {
      lookupHtml = `<div class="rc" style="margin-top:12px;border-color:rgba(34,197,94,.35)"><div class="rh"><i class="fas fa-unlock ri" style="color:var(--green)"></i><span class="rt" style="margin-left:6px">Çözüldü!</span><span class="rb"><span class="b bg">${r.lookup.source}</span></span></div><div style="font-size:22px;font-weight:800;color:var(--green);text-align:center;padding:10px;word-break:break-all;text-shadow:0 0 18px rgba(34,197,94,.4)">${r.lookup.plain}</div></div>`;
    } else if (r.lookup && r.lookup.found && r.lookup.info) {
      lookupHtml = `<div class="rc" style="margin-top:12px;border-color:rgba(0,229,255,.35)"><div class="rh"><i class="fas fa-database ri" style="color:var(--cyan)"></i><span class="rt" style="margin-left:6px">İstihbarat Kaydı</span><span class="rb"><span class="b bc">${r.lookup.source}</span></span></div><div style="font-size:12px;color:var(--text2);padding:6px 2px;word-break:break-all">${r.lookup.info}</div></div>`;
    } else {
      lookupHtml = `<div class="rc" style="margin-top:12px"><div class="rh"><i class="fas fa-lock ri" style="color:var(--yellow)"></i><span class="rt" style="margin-left:6px">Online Sözlük Taraması</span></div><div class="empty"><i class="fas fa-search"></i>Bu hash ücretsiz sözlüklerde bulunamadı</div></div>`;
    }
  }
  let genHtml = '';
  if (r.generated && Object.keys(r.generated).length) {
    genHtml = `<div class="rc" style="margin-top:12px"><div class="rh"><i class="fas fa-hashtag ri" style="color:var(--cyan)"></i><span class="rt" style="margin-left:6px">Üretilen Hash'ler</span><span class="rb"><button class="mbtn ghost" onclick="dlLast()">📥 JSON</button></span></div><table class="mt">${Object.entries(r.generated).map(([k,v])=>`<tr><td class="k">${k.toUpperCase()}</td><td style="font-size:10px;color:var(--cyan);word-break:break-all">${v}</td></tr>`).join('')}</table></div>`;
  }
  setHTML('hash-res', `
    <div class="scards">
      <div class="sc"><div class="sn" style="font-size:16px">${r.is_hash?'🔐 Hash':'📝 Metin'}</div><div class="sl">Girdi Tipi</div></div>
      <div class="sc"><div class="sn">${r.length||0}</div><div class="sl">Uzunluk</div></div>
      <div class="sc"><div class="sn" style="font-size:13px">${(r.possible_types||['?'])[0]||'?'}</div><div class="sl">Olası Algoritma</div></div>
    </div>
    <div class="rc"><div class="rh"><i class="fas fa-fingerprint ri" style="color:var(--purple)"></i><span class="rt" style="margin-left:6px">Analiz</span></div>
      <div style="margin-bottom:8px">${types||'<span class="b bgr">Bilinmiyor</span>'}</div>
      <div style="font-size:11px;color:var(--text3);word-break:break-all;font-family:monospace;background:#080808;padding:10px;border-radius:8px">${r.input}</div>
    </div>${lookupHtml}${genHtml}`);
  toast('Hash analizi tamamlandı', 'ok');
}

// ════════════════════════════════════════
// CERTINTEL
// ════════════════════════════════════════
async function doCRT() {
  const el = document.getElementById('crt-inp');
  const btn = document.getElementById('crt-btn');
  if (!el || !el.value.trim()) return;
  const domain = el.value.trim();
  if (btn) btn.disabled = true;
  show('crt-ldr');
  setHTML('crt-res', '');
  const r = await apiCall('/api/crt', {domain});
  hide('crt-ldr');
  if (btn) btn.disabled = false;
  incStat('cert');
  addRecent('CRT', domain, 'bc');
  if (r.error) {
    setHTML('crt-res', `<div class="rc"><span class="b br">⚠ ${r.error}</span></div>`);
    toast('CertIntel hatası', 'err');
    return;
  }
  setHTML('crt-res', `
    <div class="scards">
      <div class="sc"><div class="sn" style="color:var(--neon)">${r.subdomain_count||0}</div><div class="sl">Subdomain (CT)</div></div>
      <div class="sc"><div class="sn" style="color:var(--cyan)">${r.total_certs||0}</div><div class="sl">Sertifika Kaydı</div></div>
      <div class="sc"><div class="sn" style="font-size:13px">crt.sh</div><div class="sl">Kaynak</div></div>
    </div>
    <div class="rc" style="margin-bottom:10px"><div class="rh"><i class="fas fa-sitemap ri" style="color:var(--neon)"></i><span class="rt" style="margin-left:6px">Bulunan Subdomainler (${r.subdomain_count||0})</span><span class="rb"><button class="mbtn ghost" onclick="dlLast()">📥 JSON</button></span></div>
      ${!r.subdomains || !r.subdomains.length ? '<div class="empty"><i class="fas fa-times"></i>Kayıt bulunamadı</div>' : `<div style="max-height:300px;overflow-y:auto"><table class="mt"><tbody>${r.subdomains.map(x=>`<tr><td><a href="https://${x}" target="_blank" style="color:var(--cyan);text-decoration:none;font-weight:600">${x}</a></td><td style="text-align:right"><span class="b bg">CT</span></td></tr>`).join('')}</tbody></table></div>`}
    </div>
    <div class="rc"><div class="rh"><i class="fas fa-certificate ri" style="color:var(--purple)"></i><span class="rt" style="margin-left:6px">Son Sertifikalar</span></div>
      <table class="mt"><thead><tr><th>Common Name</th><th>Issuer</th><th>Bitiş</th></tr></thead><tbody>${(r.certs||[]).map(c=>`<tr><td style="color:var(--text2)">${c.common_name}</td><td style="font-size:10px;color:var(--text3);max-width:280px;overflow:hidden;text-overflow:ellipsis">${c.issuer}</td><td style="color:var(--yellow);font-size:11px">${c.not_after}</td></tr>`).join('')}</tbody></table>
    </div>`);
  toast(`CertIntel: ${r.subdomain_count||0} subdomain bulundu`, 'ok');
}

// ════════════════════════════════════════
// MAC VENDOR
// ════════════════════════════════════════
async function doMAC() {
  const el = document.getElementById('mac-inp');
  const btn = document.getElementById('mac-btn');
  if (!el || !el.value.trim()) return;
  const mac = el.value.trim();
  if (btn) btn.disabled = true;
  show('mac-ldr');
  setHTML('mac-res', '');
  const r = await apiCall('/api/mac', {mac});
  hide('mac-ldr');
  if (btn) btn.disabled = false;
  incStat('total');
  addRecent('MAC', mac, 'bp');
  if (r.error) {
    setHTML('mac-res', `<div class="rc"><span class="b br">⚠ ${r.error}</span></div>`);
    toast('MAC sorgusu hatası', 'err');
    return;
  }
  setHTML('mac-res', `
    <div class="scards">
      <div class="sc"><div class="sn" style="font-size:14px;color:var(--neon)">${r.normalized||'N/A'}</div><div class="sl">Normalize</div></div>
      <div class="sc"><div class="sn" style="font-size:13px">${r.is_local?'Evet':'Hayır'}</div><div class="sl">Local Admin Bit</div></div>
      <div class="sc"><div class="sn" style="font-size:13px">${r.is_multicast?'Evet':'Hayır'}</div><div class="sl">Multicast Bit</div></div>
    </div>
    <div class="rc"><div class="rh"><i class="fas fa-industry ri" style="color:var(--purple)"></i><span class="rt" style="margin-left:6px">Üretici (OUI)</span></div>
      <div style="font-size:18px;font-weight:700;color:${r.vendor?'var(--green)':'var(--text3)'};padding:8px 2px">${r.vendor || 'Bulunamadı — özel/rastgele adres olabilir'}</div>
    </div>`);
  toast('MAC sorgusu tamamlandı', 'ok');
}

// ════════════════════════════════════════
// ENCODE / DECODE
// ════════════════════════════════════════
async function doEncode() {
  const el   = document.getElementById('enc-inp');
  const mode = document.getElementById('enc-mode')?.value || 'b64_encode';
  if (!el || !el.value.trim()) return;
  const text = el.value;
  const r = await apiCall('/api/encode', {mode, text});
  if (r.error) {
    setHTML('enc-res', `<div class="rc"><span class="b br">⚠ ${r.error}</span></div>`);
    toast('Dönüştürme hatası', 'err');
    return;
  }
  setHTML('enc-res', `
    <div class="rc"><div class="rh"><i class="fas fa-arrow-right ri" style="color:var(--cyan)"></i><span class="rt" style="margin-left:6px">Sonuç</span><span class="rb"><button class="mbtn ghost" onclick="navigator.clipboard.writeText(${JSON.stringify(r.output||'')});toast('Kopyalandı','ok')">📋 Kopyala</button></span></div>
      <div style="font-size:13px;color:var(--green);word-break:break-all;font-family:monospace;background:#080808;padding:12px;border-radius:8px;white-space:pre-wrap">${(r.output??'').toString().replace(/</g,'&lt;')}</div>
    </div>`);
  incStat('total');
  addRecent('ENC', mode, 'bc');
  toast('Dönüştürme tamamlandı', 'ok');
}

// ════════════════════════════════════════
// v0.0.5 TOOLS
// ════════════════════════════════════════
const toolConfig = {
  'email-auth': {endpoint:'/api/email-auth', field:'domain', placeholder:'ornek.com', hint:'Alan adı girin; SPF, DMARC ve MX kayıtları incelenecek.'},
  'footprint': {endpoint:'/api/footprint', field:'target', placeholder:'ornek.com', hint:'Alan adı veya URL girin; robots.txt ve sitemap işaretleri incelenecek.'},
  'security-txt': {endpoint:'/api/security-txt', field:'target', placeholder:'ornek.com', hint:'Alan adı girin; RFC 9116 security.txt dosyası kontrol edilecek.'},
  'ioc-extract': {endpoint:'/api/ioc-extract', field:'text', placeholder:'IP, URL, e-posta veya hash içeren metni yapıştırın...', hint:'Metinden IOC çıkarılır; bu işlem ağ isteği yapmaz.'},
  'password-strength': {endpoint:'/api/password-strength', field:'password', placeholder:'Şifrenizi girin (kaydedilmez)', hint:'Şifre yalnızca yerel M-OSINT servisine iletilir ve kaydedilmez.'}
};
function setToolHint() {
  const mode = document.getElementById('tool-mode')?.value;
  const c = toolConfig[mode];
  const input = document.getElementById('tool-inp');
  const hint = document.getElementById('tool-hint');
  if (!c || !input || !hint) return;
  input.placeholder = c.placeholder;
  input.type = mode === 'password-strength' ? 'password' : 'text';
  hint.textContent = c.hint;
}
async function doTool() {
  const mode = document.getElementById('tool-mode')?.value;
  const input = document.getElementById('tool-inp');
  const button = document.getElementById('tool-btn');
  const config = toolConfig[mode];
  if (!config || !input || !input.value.trim()) return;
  if (button) button.disabled = true;
  show('tool-ldr');
  setHTML('tool-res', '');
  const body = {}; body[config.field] = input.value;
  const result = await apiCall(config.endpoint, body);
  hide('tool-ldr');
  if (button) button.disabled = false;
  incStat('total');
  addRecent('V5', mode, 'bc');
  const box = document.createElement('pre');
  box.style.cssText = 'margin:0;color:var(--green);white-space:pre-wrap;font-size:11px;font-family:monospace;word-break:break-word';
  box.textContent = JSON.stringify(result, null, 2);
  const card = document.createElement('div');
  card.className = 'rc'; card.style.marginTop = '12px';
  card.appendChild(box);
  const out = document.getElementById('tool-res');
  if (out) out.replaceChildren(card);
  toast(result.error ? 'Araç uyarısı: ' + result.error : 'v0.0.5 araç sonucu hazır', result.error ? 'err' : 'ok');
}

// ════════════════════════════════════════
// REALTIME
// ════════════════════════════════════════
function rtLog(msg, color='#4b5563') {
  const el = document.getElementById('rt-log');
  if (!el) return;
  const t = new Date().toLocaleTimeString('tr-TR');
  el.innerHTML += `<div style="color:${color}">
    <span style="color:#2d3748">[${t}]</span> ${msg}</div>`;
  el.scrollTop = el.scrollHeight;
}

function startRT() {
  const target = document.getElementById('rt-inp')?.value.trim();
  const type   = document.getElementById('rt-type')?.value;
  if (!target) return;

  document.getElementById('rt-btn').style.display  = 'none';
  document.getElementById('rt-stop').style.display = 'inline-flex';

  const log = document.getElementById('rt-log');
  if (log) log.innerHTML =
    `<span style="color:#2d3748">[ M-OSINT v0.0.5 — Gerçek Zamanlı ]</span><br><br>`;

  rtLog(`🚀 Hedef: <span style="color:#60a5fa">${target}</span> — ${type.toUpperCase()}`, '#60a5fa');
  socket.emit('realtime_scan', {target, type});
}

function stopRT() {
  document.getElementById('rt-btn').style.display  = 'inline-flex';
  document.getElementById('rt-stop').style.display = 'none';
  rtLog('⛔ Durduruldu', '#ef4444');
}

socket.on('scan_start',  d => rtLog(`▶ ${d.message}`, '#22c55e'));
socket.on('scan_result', d => {
  rtLog(`✅ Tamamlandı — ${d.type}`, '#22c55e');
  setHTML('rt-res', `
    <div class="rc" style="margin-top:12px">
      <div class="rh">
        <i class="fas fa-chart-line ri" style="color:var(--green)"></i>
        <span class="rt" style="margin-left:6px">Sonuç — ${d.type.toUpperCase()}</span>
      </div>
      <pre style="color:#22c55e;font-size:11px;white-space:pre-wrap;
                  font-family:monospace;background:#050505;
                  padding:14px;border-radius:8px">
${JSON.stringify(d.data, null, 2)}</pre>
    </div>`);
});
socket.on('scan_complete', d => {
  rtLog(`🏁 ${d.message}`, '#eab308');
  document.getElementById('rt-btn').style.display  = 'inline-flex';
  document.getElementById('rt-stop').style.display = 'none';
});
socket.on('connect',    () => rtLog('🔌 WebSocket bağlandı', '#06b6d4'));
socket.on('disconnect', () => rtLog('🔴 Bağlantı kesildi',   '#ef4444'));

// ════════════════════════════════════════
// ENTER TUŞU
// ════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  const enterMap = {
    'q-inp':  quickScan,
    'br-inp': doBreachFull,
    'pw-inp': doPassword,
    'ph-inp': doPhone,
    'un-inp': doUsername,
    'ip-inp': doIP,
    'dns-inp':doDNS,
    'pt-inp': doPort,
    'sd-inp': doSubdomain,
    'url-inp':doURL,
    'em-inp': doEmail,
    'ssl-inp': doSSL,
    'hash-inp': doHash,
    'crt-inp': doCRT,
    'mac-inp': doMAC,
    'enc-inp': doEncode,
    'tool-inp': doTool,
    'rt-inp': startRT,
  };
  Object.entries(enterMap).forEach(([id, fn]) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('keypress', e => {
      if (e.key === 'Enter') fn();
    });
  });
});
</script>
</body>
</html>"""

# ══════════════════════════════════════════
#              FLASK
# ══════════════════════════════════════════
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('MOSINT_SECRET_KEY', 'mosint-v005-local-secret')
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=f'http://{HOST}:{PORT}',
                    logger=False, engineio_logger=False)

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/breach/full',     methods=['POST'])
def api_breach_full():
    d = request.get_json(silent=True) or {}
    return jsonify(breach_full(d.get('email', '')))

@app.route('/api/breach/password', methods=['POST'])
def api_breach_password():
    d = request.get_json(silent=True) or {}
    return jsonify(breach_password(d.get('password', '')))

@app.route('/api/ip',              methods=['POST'])
def api_ip():
    d = request.get_json(silent=True) or {}
    return jsonify(ip_lookup(d.get('ip', '')))

@app.route('/api/dns',             methods=['POST'])
def api_dns():
    d = request.get_json(silent=True) or {}
    return jsonify(dns_lookup(d.get('domain', '')))

@app.route('/api/port',            methods=['POST'])
def api_port():
    d = request.get_json(silent=True) or {}
    return jsonify(port_scan(d.get('host', ''), d.get('range', 'common')))

@app.route('/api/email',           methods=['POST'])
def api_email():
    d = request.get_json(silent=True) or {}
    return jsonify(email_check(d.get('email', '')))

@app.route('/api/phone',           methods=['POST'])
def api_phone():
    d = request.get_json(silent=True) or {}
    return jsonify(phone_lookup(d.get('phone', '')))

@app.route('/api/username',        methods=['POST'])
def api_username():
    d = request.get_json(silent=True) or {}
    return jsonify(username_search(d.get('username', '')))

@app.route('/api/subdomain',       methods=['POST'])
def api_subdomain():
    d = request.get_json(silent=True) or {}
    return jsonify(subdomain_scan(d.get('domain', '')))

@app.route('/api/url',             methods=['POST'])
def api_url():
    d = request.get_json(silent=True) or {}
    return jsonify(url_analyze(d.get('url', '')))

@app.route('/api/ssl',               methods=['POST'])
def api_ssl():
    d = request.get_json(force=True, silent=True) or {}
    return jsonify(ssl_check(d.get('host', '')))

@app.route('/api/hash',              methods=['POST'])
def api_hash():
    d = request.get_json(force=True, silent=True) or {}
    return jsonify(hash_analyze(d.get('hash', '')))

@app.route('/api/crt',               methods=['POST'])
def api_crt():
    d = request.get_json(force=True, silent=True) or {}
    return jsonify(crtsh_lookup(d.get('domain', '')))

@app.route('/api/mac',               methods=['POST'])
def api_mac():
    d = request.get_json(force=True, silent=True) or {}
    return jsonify(mac_lookup(d.get('mac', '')))

@app.route('/api/encode',            methods=['POST'])
def api_encode():
    d = request.get_json(force=True, silent=True) or {}
    return jsonify(encode_decode(d.get('mode', ''), d.get('text', '')))

@app.route('/api/email-auth', methods=['POST'])
def api_email_auth():
    d = request.get_json(silent=True) or {}
    return jsonify(email_auth_check(d.get('domain', '')))

@app.route('/api/footprint', methods=['POST'])
def api_footprint():
    d = request.get_json(silent=True) or {}
    return jsonify(web_footprint(d.get('target', '')))

@app.route('/api/security-txt', methods=['POST'])
def api_security_txt():
    d = request.get_json(silent=True) or {}
    return jsonify(security_txt_check(d.get('target', '')))

@app.route('/api/ioc-extract', methods=['POST'])
def api_ioc_extract():
    d = request.get_json(silent=True) or {}
    return jsonify(ioc_extract(d.get('text', '')))

@app.route('/api/password-strength', methods=['POST'])
def api_password_strength():
    d = request.get_json(silent=True) or {}
    return jsonify(password_strength(d.get('password', '')))

@socketio.on('realtime_scan')
def handle_realtime(data):
    target = data.get('target', '')
    stype  = data.get('type',   'ip')
    emit('scan_start', {'message': f'Tarama başlatıldı → {target}'})

    def run():
        if   stype == 'ip':       res = ip_lookup(target)
        elif stype == 'port':     res = port_scan(target, 'common')
        elif stype == 'dns':      res = dns_lookup(target)
        elif stype == 'email':    res = email_check(target)
        elif stype == 'breach':   res = breach_full(target)
        elif stype == 'phone':    res = phone_lookup(target)
        elif stype == 'username': res = username_search(target)
        elif stype == 'ssl':      res = ssl_check(target)
        elif stype == 'hash':     res = hash_analyze(target)
        elif stype == 'crt':      res = crtsh_lookup(target)
        elif stype == 'mac':      res = mac_lookup(target)
        else:                     res = {}
        socketio.emit('scan_result',   {'type': stype, 'data': res})
        socketio.emit('scan_complete', {'message': 'Tamamlandı ✔'})

    threading.Thread(target=run, daemon=True).start()

if __name__ == '__main__':
    startup_animation()
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
