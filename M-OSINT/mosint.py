# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         M-OSINT Framework                            ║
# ║                       v0.0.1 (Alpha)                                 ║
# ╚══════════════════════════════════════════════════════════════════════╝

import sys
import os
import time
import threading
import re
import socket
import hashlib
import json
import concurrent.futures
import requests
import dns.resolver
import dns.reversename
import whois
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime

# ══════════════════════════════════════════
#              KONFİGÜRASYON
# ══════════════════════════════════════════

APP_NAME  = "M-OSINT"
VERSION   = "v0.0.1 (Alpha)"
HOST      = "127.0.0.1"
PORT      = 5000
DEBUG     = False

HIBP_API_KEY = ""   # opsiyonel
IPINFO_TOKEN = ""   # opsiyonel

# ══════════════════════════════════════════
#              GİRİŞ ANİMASYONU
# ══════════════════════════════════════════

def clear(): os.system("cls" if os.name == "nt" else "clear")
def color(text, code): return f"\033[{code}m{text}\033[0m"

CYAN="96"; BLUE="94"; WHITE="97"; YELLOW="93"
GREEN="92"; RED="91"; GRAY="90"; BOLD="1"

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
        print(color(line, CYAN))
        time.sleep(0.05)
    time.sleep(0.2)
    info_lines = [
        ("  ┌─────────────────────────────────────────────────────┐", BLUE),
        (f"  │   Version  : {VERSION:<38}│", CYAN),
        (f"  │   Status   : {'ALPHA - Sadece Eğitim Amaçlı':<38}│", YELLOW),
        (f"  │   Panel    : http://{HOST}:{PORT:<32}│", GREEN),
        (f"  │   Tarih    : {datetime.now().strftime('%d.%m.%Y %H:%M:%S'):<38}│", WHITE),
        ("  └─────────────────────────────────────────────────────┘", BLUE),
    ]
    for line, col in info_lines:
        print(color(line, col))
        time.sleep(0.08)
    print()
    steps = [
        "  [►] LeakCheck modülü      ",
        "  [►] HudsonRock modülü     ",
        "  [►] HIBP modülü           ",
        "  [►] IP/DNS/Port modülleri ",
        "  [►] Flask & WebSocket     ",
        "  [►] Panel hazırlanıyor    ",
    ]
    for step in steps:
        sys.stdout.write(color(step, CYAN))
        sys.stdout.flush()
        for _ in range(3):
            time.sleep(0.12)
            sys.stdout.write(color(".", BLUE))
            sys.stdout.flush()
        print(color(" OK", GREEN))
        time.sleep(0.08)
    print()
    print(color("  ✔  Sistem hazır! Panel açılıyor...", GREEN))
    print()
    print(color("  ─" * 28, GRAY))
    print(color("  [LOG]", GRAY))
    print(color("  ─" * 28, GRAY))
    print()

# ══════════════════════════════════════════
#         BREACH - LEAKCHECK.IO
# ══════════════════════════════════════════

def breach_leakcheck(email: str) -> dict:
    result = {
        "source": "LeakCheck.io",
        "found": False,
        "breach_count": 0,
        "breaches": [],
        "fields": [],
        "error": None
    }
    try:
        url = f"https://leakcheck.io/api/public?check={email}"
        r = requests.get(url, headers={"User-Agent": "M-OSINT", "Accept": "application/json"}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                result["found"]        = data.get("found", 0) > 0
                result["breach_count"] = data.get("found", 0)
                result["fields"]       = data.get("fields", [])
                for s in data.get("sources", []):
                    result["breaches"].append({
                        "name": s.get("name", ""),
                        "date": s.get("date", ""),
                    })
        elif r.status_code == 429:
            result["error"] = "Rate limit - biraz bekleyin"
        elif r.status_code == 403:
            result["error"] = "Erişim engellendi"
        else:
            result["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        result["error"] = str(e)
    return result

# ══════════════════════════════════════════
#         BREACH - HUDSONROCK
# ══════════════════════════════════════════

def breach_hudsonrock(email: str) -> dict:
    result = {
        "source": "HudsonRock Cavalier",
        "found": False,
        "stealer_count": 0,
        "stealers": [],
        "error": None
    }
    try:
        url = f"https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email={email}"
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            stealers = data.get("stealers", [])
            if stealers:
                result["found"]         = True
                result["stealer_count"] = len(stealers)
                for s in stealers[:10]:
                    result["stealers"].append({
                        "computer_name":    s.get("computer_name", "N/A"),
                        "operating_system": s.get("operating_system", "N/A"),
                        "date_compromised": s.get("date_compromised", "N/A"),
                        "malware_path":     s.get("malware_path", "N/A"),
                        "antiviruses":      s.get("antiviruses", []),
                        "credentials_count": len(s.get("credentials", [])),
                        "total_corporate":  s.get("total_corporate_services", 0),
                        "total_user":       s.get("total_user_services", 0),
                    })
        elif r.status_code == 429:
            result["error"] = "Rate limit"
        else:
            result["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        result["error"] = str(e)
    return result

# ══════════════════════════════════════════
#         BREACH - HIBP PUBLIC
# ══════════════════════════════════════════

def breach_hibp_public(email: str) -> dict:
    result = {
        "source": "HIBP Public",
        "found": False,
        "breach_count": 0,
        "breaches": [],
        "total_in_db": 0,
        "error": None
    }
    try:
        r = requests.get(
            "https://haveibeenpwned.com/api/v3/breaches",
            headers={"User-Agent": "M-OSINT"},
            timeout=15
        )
        if r.status_code == 200:
            all_b = r.json()
            result["total_in_db"] = len(all_b)
            domain = email.split("@")[1].lower() if "@" in email else ""
            for b in all_b:
                bd = b.get("Domain", "").lower()
                if bd and domain and (bd == domain or domain in bd or bd in domain):
                    result["found"] = True
                    result["breaches"].append({
                        "name":       b.get("Name", ""),
                        "domain":     b.get("Domain", ""),
                        "date":       b.get("BreachDate", ""),
                        "count":      b.get("PwnCount", 0),
                        "data_types": b.get("DataClasses", []),
                    })
            result["breach_count"] = len(result["breaches"])
        else:
            result["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        result["error"] = str(e)
    return result

# ══════════════════════════════════════════
#         BREACH - ŞİFRE (HIBP)
# ══════════════════════════════════════════

def breach_password(password: str) -> dict:
    result = {"pwned": False, "count": 0, "error": None}
    try:
        sha1   = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        r = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"User-Agent": "M-OSINT", "Add-Padding": "true"},
            timeout=10
        )
        if r.status_code == 200:
            for line in r.text.splitlines():
                if ":" not in line: continue
                h, c = line.split(":", 1)
                if h.strip().upper() == suffix:
                    result["pwned"] = True
                    result["count"] = int(c.strip())
                    break
        else:
            result["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        result["error"] = str(e)
    return result

# ══════════════════════════════════════════
#         BREACH - TAM EMAIL TARAMA
# ══════════════════════════════════════════

def breach_full(email: str) -> dict:
    """3 kaynaktan aynı anda sorgular"""
    result = {
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

    # Paralel sorgula
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_lc = ex.submit(breach_leakcheck,   email)
        f_hr = ex.submit(breach_hudsonrock,  email)
        f_hb = ex.submit(breach_hibp_public, email)

        result["leakcheck"]  = f_lc.result()
        result["hudsonrock"] = f_hr.result()
        result["hibp"]       = f_hb.result()

    # Özet
    if result["leakcheck"].get("found"):
        result["summary"]["sources_with_data"] += 1
        result["summary"]["total_breaches"]    += result["leakcheck"]["breach_count"]
    if result["hudsonrock"].get("found"):
        result["summary"]["sources_with_data"] += 1
        result["summary"]["infostealer_found"]  = True
    if result["hibp"].get("found"):
        result["summary"]["sources_with_data"] += 1
        result["summary"]["total_breaches"]    += result["hibp"]["breach_count"]

    return result

# ══════════════════════════════════════════
#              IP MODÜLÜ
# ══════════════════════════════════════════

def ip_lookup(ip: str) -> dict:
    result = {"ip": ip, "info": {}, "asn": {}, "blacklist": {}, "error": None}
    try:
        url = f"https://ipinfo.io/{ip}/json"
        if IPINFO_TOKEN: url += f"?token={IPINFO_TOKEN}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            result["info"] = {
                "ip":       d.get("ip"),
                "hostname": d.get("hostname", "N/A"),
                "city":     d.get("city", "N/A"),
                "region":   d.get("region", "N/A"),
                "country":  d.get("country", "N/A"),
                "location": d.get("loc", "N/A"),
                "org":      d.get("org", "N/A"),
                "postal":   d.get("postal", "N/A"),
                "timezone": d.get("timezone", "N/A"),
            }
            org = d.get("org", "")
            if org:
                parts = org.split(" ", 1)
                result["asn"] = {
                    "asn": parts[0] if parts else "N/A",
                    "org": parts[1] if len(parts) > 1 else "N/A",
                }
    except Exception as e:
        result["error"] = str(e)

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
    result["blacklist"] = bl
    return result

# ══════════════════════════════════════════
#              DNS MODÜLÜ
# ══════════════════════════════════════════

def dns_lookup(domain: str) -> dict:
    result = {"domain": domain, "records": {}, "whois": {}, "error": None}
    for rtype in ["A","AAAA","MX","NS","TXT","CNAME","SOA"]:
        try:
            ans = dns.resolver.resolve(domain, rtype, lifetime=5)
            result["records"][rtype] = [str(r) for r in ans]
        except dns.resolver.NXDOMAIN:
            result["records"][rtype] = ["NXDOMAIN"]
        except dns.resolver.NoAnswer:
            result["records"][rtype] = []
        except Exception as e:
            result["records"][rtype] = [str(e)]
    try:
        w = whois.whois(domain)
        result["whois"] = {
            "registrar":       str(w.registrar)       if w.registrar       else "N/A",
            "creation_date":   str(w.creation_date)   if w.creation_date   else "N/A",
            "expiration_date": str(w.expiration_date) if w.expiration_date else "N/A",
            "name_servers":    list(w.name_servers)   if w.name_servers    else [],
            "emails":          w.emails               if w.emails          else [],
            "country":         str(w.country)         if w.country         else "N/A",
        }
    except Exception as e:
        result["whois"] = {"error": str(e)}
    return result

# ══════════════════════════════════════════
#              PORT MODÜLÜ
# ══════════════════════════════════════════

COMMON_PORTS = {
    21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",
    80:"HTTP",110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",
    3306:"MySQL",3389:"RDP",5432:"PostgreSQL",6379:"Redis",
    8080:"HTTP-Alt",8443:"HTTPS-Alt",27017:"MongoDB",
    9200:"Elasticsearch",1433:"MSSQL",5900:"VNC",
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
                    "service": COMMON_PORTS.get(port,"Unknown"), "banner": banner}
        s.close()
    except: pass
    return {"port": port, "open": False}

def port_scan(host: str, port_range: str = "common") -> dict:
    result = {"host": host, "ip": None, "open_ports": [],
              "closed_count": 0, "scan_time": None, "error": None}
    start = datetime.now()
    try:
        result["ip"] = socket.gethostbyname(host)
    except Exception as e:
        result["error"] = str(e)
        return result

    if port_range == "common":      ports = list(COMMON_PORTS.keys())
    elif port_range == "top100":    ports = list(range(1, 101))
    elif port_range == "top1000":   ports = list(range(1, 1001))
    else:
        try:
            s, e = map(int, port_range.split("-"))
            ports = list(range(s, e+1))
        except: ports = list(COMMON_PORTS.keys())

    open_ports, closed = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as ex:
        futures = {ex.submit(check_port, result["ip"], p): p for p in ports}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r["open"]: open_ports.append(r)
            else: closed += 1

    result["open_ports"]   = sorted(open_ports, key=lambda x: x["port"])
    result["closed_count"] = closed
    result["scan_time"]    = str(datetime.now() - start)
    return result

# ══════════════════════════════════════════
#              EMAIL MODÜLÜ
# ══════════════════════════════════════════

def email_check(email: str) -> dict:
    result = {
        "email": email, "format_valid": False, "domain_valid": False,
        "mx_records": [], "disposable": False, "free_provider": False,
        "gravatar": {}, "social_guess": {}, "error": None
    }
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        result["error"] = "Geçersiz format"
        return result
    result["format_valid"] = True
    domain = email.split("@")[1]
    try:
        mx = dns.resolver.resolve(domain, "MX", lifetime=5)
        result["mx_records"]  = [str(r.exchange) for r in mx]
        result["domain_valid"] = True
    except: result["domain_valid"] = False

    result["disposable"]    = domain.lower() in ["tempmail.com","guerrillamail.com","mailinator.com","yopmail.com"]
    result["free_provider"] = domain.lower() in ["gmail.com","yahoo.com","hotmail.com","outlook.com","yandex.com","protonmail.com"]

    try:
        h  = hashlib.md5(email.lower().encode()).hexdigest()
        gr = requests.get(f"https://www.gravatar.com/avatar/{h}?d=404", timeout=5)
        result["gravatar"] = {"exists": gr.status_code == 200,
                              "url": f"https://www.gravatar.com/avatar/{h}"}
    except: result["gravatar"] = {"exists": False, "url": None}

    u = email.split("@")[0]
    result["social_guess"] = {
        "github":    f"https://github.com/{u}",
        "twitter":   f"https://twitter.com/{u}",
        "instagram": f"https://instagram.com/{u}",
        "reddit":    f"https://reddit.com/user/{u}",
    }
    return result

# ══════════════════════════════════════════
#              HTML - TAM ARAYÜZ
# ══════════════════════════════════════════

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>M-OSINT {{ version }}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.0/socket.io.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
:root{
  --bg0:#020b18;--bg1:#040f20;--bg2:#071428;--bg3:#0a1a30;
  --blue:#0d6efd;--blue2:#0a58ca;--cyan:#00c8ff;--cyan2:#0099cc;
  --green:#00e676;--red:#ff1744;--yellow:#ffd600;--orange:#ff6d00;
  --purple:#7c4dff;--text:#c9d8f0;--muted:#4a6080;--border:#0d2040;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{background:var(--bg0);color:var(--text);font-family:'Segoe UI',monospace;display:flex}
#sidebar{width:220px;min-width:220px;background:var(--bg1);border-right:1px solid var(--border);
  display:flex;flex-direction:column;height:100vh;overflow:hidden;}
.sb-logo{padding:20px 16px;border-bottom:1px solid var(--border);
  background:linear-gradient(135deg,rgba(0,200,255,.08),rgba(13,110,253,.05));}
.sb-logo .logo{font-size:22px;font-weight:900;letter-spacing:4px;
  background:linear-gradient(90deg,var(--cyan),var(--blue));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.sb-logo .ver{font-size:10px;color:var(--muted);margin-top:2px;letter-spacing:1px;}
.sb-section{padding:14px 16px 4px;font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:2px;}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 16px;color:var(--muted);
  text-decoration:none;font-size:13px;border-left:2px solid transparent;transition:all .18s;cursor:pointer;}
.nav-item:hover,.nav-item.active{color:var(--cyan);background:rgba(0,200,255,.05);border-left-color:var(--cyan);}
.nav-item i{width:16px;text-align:center;font-size:12px}
.sb-bottom{padding:14px 16px;border-top:1px solid var(--border);margin-top:auto;font-size:10px;color:var(--muted);}
.online-dot{width:6px;height:6px;border-radius:50%;background:var(--green);display:inline-block;animation:blink 1.5s infinite;margin-right:4px;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
#main{flex:1;display:flex;flex-direction:column;height:100vh;overflow:hidden}
#topbar{background:var(--bg1);border-bottom:1px solid var(--border);padding:12px 24px;
  display:flex;align-items:center;justify-content:space-between;flex-shrink:0;}
#topbar .title{font-size:14px;font-weight:700;color:var(--text);letter-spacing:1px}
#topbar .right{display:flex;align-items:center;gap:16px;font-size:12px;color:var(--muted)}
#content{flex:1;overflow-y:auto;padding:20px 24px}
#content::-webkit-scrollbar{width:5px}
#content::-webkit-scrollbar-track{background:var(--bg0)}
#content::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.page{display:none}.page.active{display:block}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;
  padding:18px;margin-bottom:16px;position:relative;overflow:hidden;}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--blue),transparent);opacity:.4;}
.card-hdr{display:flex;align-items:center;gap:8px;margin-bottom:14px;
  padding-bottom:10px;border-bottom:1px solid var(--border);}
.card-hdr i{color:var(--cyan);font-size:13px}
.card-hdr span{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--text)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.stat{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:16px;text-align:center;transition:border-color .2s;}
.stat:hover{border-color:var(--cyan2)}
.stat .num{font-size:26px;font-weight:900;color:var(--cyan)}
.stat .lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:4px}
.row{display:flex;gap:8px;margin-bottom:12px}
.m-inp{flex:1;background:var(--bg0);border:1px solid var(--border);color:var(--text);
  padding:9px 13px;border-radius:6px;font-size:13px;font-family:inherit;outline:none;transition:border-color .2s;}
.m-inp:focus{border-color:var(--cyan);box-shadow:0 0 8px rgba(0,200,255,.12)}
.m-sel{background:var(--bg0);border:1px solid var(--border);color:var(--text);
  padding:9px 12px;border-radius:6px;font-size:13px;font-family:inherit;outline:none;cursor:pointer;}
.m-btn{background:linear-gradient(135deg,var(--blue),var(--blue2));color:#fff;border:none;
  padding:9px 18px;border-radius:6px;font-size:12px;font-weight:700;font-family:inherit;
  cursor:pointer;letter-spacing:1px;text-transform:uppercase;transition:all .2s;white-space:nowrap;}
.m-btn:hover{background:linear-gradient(135deg,var(--cyan2),var(--blue));box-shadow:0 0 14px rgba(0,200,255,.25)}
.m-btn:disabled{opacity:.4;cursor:not-allowed}
.m-btn.red{background:linear-gradient(135deg,#c62828,#b71c1c)}
.m-btn.green{background:linear-gradient(135deg,#1b5e20,#2e7d32)}
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;}
.bd-red{background:rgba(255,23,68,.12);color:var(--red);border:1px solid rgba(255,23,68,.25)}
.bd-green{background:rgba(0,230,118,.12);color:var(--green);border:1px solid rgba(0,230,118,.25)}
.bd-blue{background:rgba(0,200,255,.12);color:var(--cyan);border:1px solid rgba(0,200,255,.25)}
.bd-yellow{background:rgba(255,214,0,.12);color:var(--yellow);border:1px solid rgba(255,214,0,.25)}
.bd-purple{background:rgba(124,77,255,.12);color:var(--purple);border:1px solid rgba(124,77,255,.25)}
.bd-orange{background:rgba(255,109,0,.12);color:var(--orange);border:1px solid rgba(255,109,0,.25)}
.m-tbl{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
.m-tbl th{padding:8px 12px;background:var(--bg3);color:var(--muted);font-size:10px;
  text-transform:uppercase;letter-spacing:1px;text-align:left;border-bottom:1px solid var(--border)}
.m-tbl td{padding:8px 12px;border-bottom:1px solid rgba(13,32,64,.8);color:var(--text);vertical-align:top}
.m-tbl tr:hover td{background:rgba(0,200,255,.02)}
.loader{display:none;padding:16px;text-align:center;color:var(--cyan);font-size:13px}
.spin{width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--cyan);
  border-radius:50%;animation:spin .7s linear infinite;display:inline-block;margin-right:8px;}
@keyframes spin{to{transform:rotate(360deg)}}
.terminal{background:var(--bg0);border:1px solid var(--border);border-radius:6px;
  padding:14px;height:360px;overflow-y:auto;font-size:12px;font-family:'Courier New',monospace;line-height:1.7;}
.terminal::-webkit-scrollbar{width:4px}
.terminal::-webkit-scrollbar-thumb{background:var(--border)}
.mod-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:16px;
  cursor:pointer;transition:all .2s;text-decoration:none;display:block;position:relative;overflow:hidden;}
.mod-card:hover{border-color:var(--cyan);transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,200,255,.1)}
.mod-card .mc-icon{font-size:22px;margin-bottom:10px}
.mod-card .mc-title{font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px}
.mod-card .mc-desc{font-size:11px;color:var(--muted);line-height:1.5}
.res-box{background:var(--bg0);border:1px solid var(--border);border-radius:6px;
  padding:14px;min-height:80px;font-size:12px;margin-top:10px;}
/* source badge bar */
.src-bar{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;}
.src-card{background:var(--bg3);border:1px solid var(--border);border-radius:6px;
  padding:10px 14px;flex:1;min-width:180px;}
.src-card .sc-title{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;}
.src-card .sc-val{font-size:18px;font-weight:900;}
/* infostealer card */
.stealer-card{background:var(--bg3);border:1px solid rgba(255,23,68,.2);border-radius:6px;
  padding:12px;margin-bottom:8px;}
.stealer-card .sc-head{font-size:12px;font-weight:700;color:var(--red);margin-bottom:6px;}
body::after{content:'';position:fixed;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--blue),var(--cyan),var(--blue),transparent);
  animation:glowline 4s linear infinite;pointer-events:none;z-index:9999;}
@keyframes glowline{0%{background-position:0%}100%{background-position:200%}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<div id="sidebar">
  <div class="sb-logo">
    <div class="logo">M-OSINT</div>
    <div class="ver">{{ version }} &nbsp;|&nbsp; ALPHA</div>
  </div>
  <div class="sb-section">Ana</div>
  <div class="nav-item active" onclick="goPage('dash',this)">
    <i class="fas fa-th-large"></i> Dashboard
  </div>
  <div class="sb-section">Modüller</div>
  <div class="nav-item" onclick="goPage('breach',this)">
    <i class="fas fa-database"></i> Breach & Leak
  </div>
  <div class="nav-item" onclick="goPage('password',this)">
    <i class="fas fa-key"></i> Şifre Kontrolü
  </div>
  <div class="nav-item" onclick="goPage('email',this)">
    <i class="fas fa-envelope"></i> Email Analiz
  </div>
  <div class="nav-item" onclick="goPage('ip',this)">
    <i class="fas fa-globe"></i> IP Sorgu
  </div>
  <div class="nav-item" onclick="goPage('dns',this)">
    <i class="fas fa-server"></i> DNS Sorgu
  </div>
  <div class="nav-item" onclick="goPage('port',this)">
    <i class="fas fa-plug"></i> Port Tarama
  </div>
  <div class="nav-item" onclick="goPage('realtime',this)">
    <i class="fas fa-satellite-dish"></i> Gerçek Zamanlı
  </div>
  <div class="sb-section">Sistem</div>
  <div class="nav-item" onclick="goPage('settings',this)">
    <i class="fas fa-cog"></i> Ayarlar
  </div>
  <div class="sb-bottom">
    <span class="online-dot"></span>
    Sistem Aktif &nbsp;|&nbsp; <span id="clock"></span>
  </div>
</div>

<!-- MAIN -->
<div id="main">
  <div id="topbar">
    <div class="title" id="page-title">
      <i class="fas fa-th-large" style="color:var(--cyan);margin-right:8px"></i>DASHBOARD
    </div>
    <div class="right">
      <span><i class="fas fa-shield-alt" style="color:var(--green)"></i> &nbsp;M-OSINT</span>
      <span style="color:var(--border)">|</span>
      <span id="scan-count">Sorgu: 0</span>
    </div>
  </div>

  <div id="content">

    <!-- ══ DASHBOARD ══ -->
    <div class="page active" id="page-dash">
      <div class="g4" style="margin-bottom:16px">
        <div class="stat"><div class="num" id="s-total">0</div><div class="lbl">Toplam Sorgu</div></div>
        <div class="stat"><div class="num" style="color:var(--red)" id="s-breach">0</div><div class="lbl">Breach Bulundu</div></div>
        <div class="stat"><div class="num" style="color:var(--orange)" id="s-stealer">0</div><div class="lbl">Infostealer</div></div>
        <div class="stat"><div class="num" style="color:var(--green)" id="s-open">0</div><div class="lbl">Açık Port</div></div>
      </div>
      <div class="g2">
        <div class="card">
          <div class="card-hdr"><i class="fas fa-bolt"></i><span>Hızlı Sorgu</span></div>
          <div class="row">
            <input class="m-inp" id="q-inp" placeholder="IP, domain veya email...">
            <select class="m-sel" id="q-type">
              <option value="ip">IP</option>
              <option value="dns">DNS</option>
              <option value="email">Email</option>
              <option value="port">Port</option>
              <option value="breach">Breach</option>
            </select>
            <button class="m-btn" onclick="quickScan()">TARA</button>
          </div>
          <div class="loader" id="q-loader"><span class="spin"></span>Sorgulanıyor...</div>
          <div class="res-box" id="q-res" style="color:var(--muted)">Sonuç burada görünecek...</div>
        </div>
        <div class="card">
          <div class="card-hdr"><i class="fas fa-history"></i><span>Son Sorgular</span></div>
          <div id="recent-list" style="font-size:12px;color:var(--muted)">Henüz sorgu yapılmadı.</div>
        </div>
      </div>
      <div class="g3">
        <div class="mod-card" onclick="goPage('breach',document.querySelectorAll('.nav-item')[1])">
          <div class="mc-icon" style="color:var(--red)">🔓</div>
          <div class="mc-title">Breach & Leak</div>
          <div class="mc-desc">LeakCheck + HudsonRock + HIBP — 3 kaynak aynı anda</div>
        </div>
        <div class="mod-card" onclick="goPage('password',document.querySelectorAll('.nav-item')[2])">
          <div class="mc-icon" style="color:var(--yellow)">🔑</div>
          <div class="mc-title">Şifre Kontrolü</div>
          <div class="mc-desc">HIBP k-Anonymity ile şifre sızıntı taraması</div>
        </div>
        <div class="mod-card" onclick="goPage('email',document.querySelectorAll('.nav-item')[3])">
          <div class="mc-icon" style="color:var(--purple)">📧</div>
          <div class="mc-title">Email Analiz</div>
          <div class="mc-desc">MX, Gravatar, format ve sosyal medya tahmini</div>
        </div>
        <div class="mod-card" onclick="goPage('ip',document.querySelectorAll('.nav-item')[4])">
          <div class="mc-icon" style="color:var(--cyan)">🌐</div>
          <div class="mc-title">IP Sorgu</div>
          <div class="mc-desc">Konum, ISP, ASN ve blacklist kontrolü</div>
        </div>
        <div class="mod-card" onclick="goPage('dns',document.querySelectorAll('.nav-item')[5])">
          <div class="mc-icon" style="color:var(--green)">🖥</div>
          <div class="mc-title">DNS Sorgu</div>
          <div class="mc-desc">A, MX, NS, TXT kayıtları ve WHOIS</div>
        </div>
        <div class="mod-card" onclick="goPage('port',document.querySelectorAll('.nav-item')[6])">
          <div class="mc-icon" style="color:var(--orange)">🔌</div>
          <div class="mc-title">Port Tarama</div>
          <div class="mc-desc">TCP tarama ve banner grabbing</div>
        </div>
      </div>
    </div>

    <!-- ══ BREACH ══ -->
    <div class="page" id="page-breach">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-database" style="color:var(--red)"></i>
          <span>Email Breach Tarama — 3 Kaynak</span>
        </div>
        <p style="font-size:12px;color:var(--muted);margin-bottom:12px">
          LeakCheck.io &nbsp;+&nbsp; HudsonRock Cavalier &nbsp;+&nbsp; HIBP Public — aynı anda taranır
        </p>
        <div class="row">
          <input class="m-inp" id="br-email" placeholder="hedef@domain.com">
          <button class="m-btn red" onclick="doBreachFull()" id="br-btn">
            <i class="fas fa-search"></i> TARA
          </button>
        </div>
        <div class="loader" id="br-loader">
          <span class="spin"></span>3 kaynak taranıyor... (LeakCheck + HudsonRock + HIBP)
        </div>
        <div id="br-res"></div>
      </div>
    </div>

    <!-- ══ PASSWORD ══ -->
    <div class="page" id="page-password">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-key" style="color:var(--yellow)"></i>
          <span>Şifre Sızıntı Kontrolü</span>
        </div>
        <p style="font-size:12px;color:var(--muted);margin-bottom:12px">
          🔒 k-Anonymity modeli — şifreniz asla gönderilmez, sadece SHA1 hash'in ilk 5 karakteri kullanılır
        </p>
        <div class="row">
          <input class="m-inp" id="pw-inp" type="password" placeholder="Kontrol edilecek şifreyi girin...">
          <button class="m-btn" onclick="doPassword()">KONTROL ET</button>
        </div>
        <div class="loader" id="pw-loader"><span class="spin"></span>Kontrol ediliyor...</div>
        <div id="pw-res"></div>
      </div>
    </div>

    <!-- ══ EMAIL ══ -->
    <div class="page" id="page-email">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-envelope" style="color:var(--purple)"></i><span>Email Analiz</span></div>
        <div class="row">
          <input class="m-inp" id="em-inp" placeholder="hedef@domain.com">
          <button class="m-btn" onclick="doEmail()">ANALİZ ET</button>
        </div>
        <div class="loader" id="em-loader"><span class="spin"></span>Analiz ediliyor...</div>
        <div id="em-res"></div>
      </div>
    </div>

    <!-- ══ IP ══ -->
    <div class="page" id="page-ip">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-globe" style="color:var(--cyan)"></i><span>IP Sorgu</span></div>
        <div class="row">
          <input class="m-inp" id="ip-inp" placeholder="8.8.8.8 veya domain.com">
          <button class="m-btn" onclick="doIP()">SORGULA</button>
        </div>
        <div class="loader" id="ip-loader"><span class="spin"></span>Sorgulanıyor...</div>
      </div>
      <div id="ip-res"></div>
    </div>

    <!-- ══ DNS ══ -->
    <div class="page" id="page-dns">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-server" style="color:var(--green)"></i><span>DNS Sorgu</span></div>
        <div class="row">
          <input class="m-inp" id="dns-inp" placeholder="ornek.com">
          <button class="m-btn" onclick="doDNS()">SORGULA</button>
        </div>
        <div class="loader" id="dns-loader"><span class="spin"></span>Sorgulanıyor...</div>
      </div>
      <div id="dns-res"></div>
    </div>

    <!-- ══ PORT ══ -->
    <div class="page" id="page-port">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-plug" style="color:var(--yellow)"></i><span>Port Tarama</span></div>
        <div class="row">
          <input class="m-inp" id="pt-inp" placeholder="192.168.1.1 veya domain.com">
          <select class="m-sel" id="pt-range">
            <option value="common">Yaygın Portlar</option>
            <option value="top100">İlk 100</option>
            <option value="top1000">İlk 1000</option>
          </select>
          <button class="m-btn" onclick="doPort()" id="pt-btn">TARA</button>
        </div>
        <div class="loader" id="pt-loader"><span class="spin"></span>Taranıyor... Lütfen bekleyin</div>
      </div>
      <div id="pt-res"></div>
    </div>

    <!-- ══ REALTIME ══ -->
    <div class="page" id="page-realtime">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-satellite-dish" style="color:var(--orange)"></i><span>Gerçek Zamanlı</span></div>
        <div class="row">
          <input class="m-inp" id="rt-inp" placeholder="Hedef girin...">
          <select class="m-sel" id="rt-type">
            <option value="ip">IP</option>
            <option value="port">Port</option>
            <option value="dns">DNS</option>
            <option value="email">Email</option>
            <option value="breach">Breach</option>
          </select>
          <button class="m-btn" onclick="startRT()" id="rt-btn">BAŞLAT</button>
          <button class="m-btn red" onclick="stopRT()" id="rt-stop" style="display:none">DURDUR</button>
        </div>
        <div class="terminal" id="rt-log">
          <span style="color:var(--muted)">[ M-OSINT Gerçek Zamanlı Terminal ]</span><br>
          <span style="color:var(--muted)">Hedef girin ve başlat butonuna basın...</span><br>
        </div>
      </div>
      <div id="rt-res"></div>
    </div>

    <!-- ══ SETTINGS ══ -->
    <div class="page" id="page-settings">
      <div class="card">
        <div class="card-hdr"><i class="fas fa-plug"></i><span>Servis Durumları</span></div>
        <table class="m-tbl">
          <thead><tr><th>Servis</th><th>Amaç</th><th>Durum</th><th>Limit</th></tr></thead>
          <tbody>
            <tr><td>LeakCheck.io</td><td>Email breach</td>
              <td><span class="badge bd-green">✅ Aktif</span></td>
              <td style="color:var(--muted)">Günde ~10 ücretsiz sorgu</td></tr>
            <tr><td>HudsonRock</td><td>Infostealer tarama</td>
              <td><span class="badge bd-green">✅ Aktif</span></td>
              <td style="color:var(--muted)">Ücretsiz, rate limit var</td></tr>
            <tr><td>HIBP Public</td><td>Domain breach listesi</td>
              <td><span class="badge bd-green">✅ Aktif</span></td>
              <td style="color:var(--muted)">Ücretsiz</td></tr>
            <tr><td>HIBP PwnedPasswords</td><td>Şifre kontrolü</td>
              <td><span class="badge bd-green">✅ Aktif</span></td>
              <td style="color:var(--muted)">Tamamen ücretsiz</td></tr>
            <tr><td>ipinfo.io</td><td>IP bilgisi</td>
              <td><span class="badge bd-green">✅ Aktif</span></td>
              <td style="color:var(--muted)">Aylık 50k ücretsiz</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-hdr"><i class="fas fa-info-circle"></i><span>Hakkında</span></div>
        <div style="font-size:13px;line-height:2.2">
          <div><span style="color:var(--muted)">Uygulama &nbsp;:</span> M-OSINT</div>
          <div><span style="color:var(--muted)">Versiyon &nbsp;:</span> {{ version }}</div>
          <div><span style="color:var(--muted)">Amaç &nbsp;&nbsp;&nbsp;&nbsp;:</span>
            <span style="color:var(--yellow)">Sadece Eğitim Amaçlı</span></div>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
const socket = io();
let scanCount=0, recentScans=[];
let stats={total:0,breach:0,stealer:0,open:0};

// ── CLOCK ──
setInterval(()=>{
  document.getElementById('clock').textContent=
    new Date().toLocaleTimeString('tr-TR',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
},1000);

// ── PAGE NAV ──
function goPage(name,el){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  if(el) el.classList.add('active');
  const titles={
    dash:'<i class="fas fa-th-large" style="color:var(--cyan);margin-right:8px"></i>DASHBOARD',
    breach:'<i class="fas fa-database" style="color:var(--red);margin-right:8px"></i>BREACH & LEAK',
    password:'<i class="fas fa-key" style="color:var(--yellow);margin-right:8px"></i>ŞİFRE KONTROLÜ',
    email:'<i class="fas fa-envelope" style="color:var(--purple);margin-right:8px"></i>EMAIL ANALİZ',
    ip:'<i class="fas fa-globe" style="color:var(--cyan);margin-right:8px"></i>IP SORGU',
    dns:'<i class="fas fa-server" style="color:var(--green);margin-right:8px"></i>DNS SORGU',
    port:'<i class="fas fa-plug" style="color:var(--yellow);margin-right:8px"></i>PORT TARAMA',
    realtime:'<i class="fas fa-satellite-dish" style="color:var(--orange);margin-right:8px"></i>GERÇEK ZAMANLI',
    settings:'<i class="fas fa-cog" style="color:var(--muted);margin-right:8px"></i>AYARLAR',
  };
  document.getElementById('page-title').innerHTML=titles[name]||name.toUpperCase();
}

// ── API ──
async function api(ep,data){
  const r=await fetch(ep,{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  return r.json();
}
function show(id){document.getElementById(id).style.display='block'}
function hide(id){document.getElementById(id).style.display='none'}

function incStat(key,val=1){
  stats[key]+=val; stats.total++;
  document.getElementById('s-total').textContent=stats.total;
  document.getElementById('s-breach').textContent=stats.breach;
  document.getElementById('s-stealer').textContent=stats.stealer;
  document.getElementById('s-open').textContent=stats.open;
  scanCount++;
  document.getElementById('scan-count').textContent='Sorgu: '+scanCount;
}

function addRecent(type,target){
  recentScans.unshift({type,target,time:new Date().toLocaleTimeString('tr-TR')});
  if(recentScans.length>8) recentScans.pop();
  document.getElementById('recent-list').innerHTML=recentScans.map(s=>`
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:6px 0;border-bottom:1px solid var(--border);">
      <span><span class="badge bd-blue">${s.type.toUpperCase()}</span>
        <span style="margin-left:8px;font-size:12px">${s.target}</span></span>
      <span style="color:var(--muted);font-size:11px">${s.time}</span>
    </div>`).join('');
}

// ── QUICK SCAN ──
async function quickScan(){
  const inp=document.getElementById('q-inp').value.trim();
  const type=document.getElementById('q-type').value;
  if(!inp) return;
  show('q-loader'); document.getElementById('q-res').innerHTML='';
  const map={
    ip:['/api/ip',{ip:inp}],
    dns:['/api/dns',{domain:inp}],
    email:['/api/email',{email:inp}],
    port:['/api/port',{host:inp,range:'common'}],
    breach:['/api/breach/full',{email:inp}],
  };
  const [ep,data]=map[type];
  const res=await api(ep,data);
  hide('q-loader');
  document.getElementById('q-res').innerHTML=
    `<pre style="color:var(--green);white-space:pre-wrap;font-size:11px">${JSON.stringify(res,null,2)}</pre>`;
  incStat('total'); addRecent(type,inp);
}

// ── BREACH FULL ──
async function doBreachFull(){
  const email=document.getElementById('br-email').value.trim();
  if(!email) return;
  document.getElementById('br-btn').disabled=true;
  show('br-loader'); document.getElementById('br-res').innerHTML='';

  const r=await api('/api/breach/full',{email});
  hide('br-loader');
  document.getElementById('br-btn').disabled=false;

  const sum=r.summary||{};
  const lc=r.leakcheck||{};
  const hr=r.hudsonrock||{};
  const hb=r.hibp||{};

  // İstatistik güncelle
  if(sum.total_breaches>0) incStat('breach', sum.total_breaches);
  if(hr.found) incStat('stealer', hr.stealer_count||1);
  addRecent('breach', email);

  let html=`
  <!-- Özet -->
  <div class="src-bar">
    <div class="src-card">
      <div class="sc-title">Toplam Breach</div>
      <div class="sc-val" style="color:${sum.total_breaches>0?'var(--red)':'var(--green)'}">
        ${sum.total_breaches||0}
      </div>
    </div>
    <div class="src-card">
      <div class="sc-title">Infostealer</div>
      <div class="sc-val" style="color:${hr.found?'var(--orange)':'var(--green)'}">
        ${hr.found ? (hr.stealer_count+' Kayıt') : 'Temiz'}
      </div>
    </div>
    <div class="src-card">
      <div class="sc-title">Kaynaklar</div>
      <div class="sc-val" style="color:var(--cyan)">${sum.sources_with_data||0}/3</div>
    </div>
  </div>

  <!-- LeakCheck -->
  <div class="card" style="margin-bottom:12px">
    <div class="card-hdr">
      <i class="fas fa-search" style="color:${lc.found?'var(--red)':'var(--green)'}"></i>
      <span>LeakCheck.io</span>
      ${lc.found
        ? `<span class="badge bd-red" style="margin-left:auto">🚨 ${lc.breach_count} Breach</span>`
        : `<span class="badge bd-green" style="margin-left:auto">✅ Temiz</span>`}
    </div>
    ${lc.error ? `<div style="color:var(--yellow);font-size:12px">⚠ ${lc.error}</div>` : ''}
    ${lc.fields&&lc.fields.length>0 ? `
      <div style="margin-bottom:10px">
        <span style="font-size:11px;color:var(--muted)">Sızan Alanlar: </span>
        ${lc.fields.map(f=>`<span class="badge bd-yellow" style="margin:2px">${f}</span>`).join('')}
      </div>` : ''}
    ${lc.breaches&&lc.breaches.length>0 ? `
      <table class="m-tbl">
        <thead><tr><th>Site / Servis</th><th>Tarih</th></tr></thead>
        <tbody>
          ${lc.breaches.map(b=>`
            <tr>
              <td><strong style="color:var(--text)">${b.name}</strong></td>
              <td style="color:var(--muted)">${b.date||'Bilinmiyor'}</td>
            </tr>`).join('')}
        </tbody>
      </table>` : ''}
  </div>

  <!-- HudsonRock -->
  <div class="card" style="margin-bottom:12px">
    <div class="card-hdr">
      <i class="fas fa-bug" style="color:${hr.found?'var(--orange)':'var(--green)'}"></i>
      <span>HudsonRock Cavalier — Infostealer</span>
      ${hr.found
        ? `<span class="badge bd-orange" style="margin-left:auto">🦠 ${hr.stealer_count} Enfekte Cihaz</span>`
        : `<span class="badge bd-green" style="margin-left:auto">✅ Temiz</span>`}
    </div>
    ${hr.error ? `<div style="color:var(--yellow);font-size:12px">⚠ ${hr.error}</div>` : ''}
    ${hr.stealers&&hr.stealers.length>0 ? `
      ${hr.stealers.map(s=>`
        <div class="stealer-card">
          <div class="sc-head">🦠 Enfekte Cihaz</div>
          <table class="m-tbl">
            <tr><td style="color:var(--muted);width:40%">Bilgisayar</td>
                <td style="color:var(--text)">${s.computer_name}</td></tr>
            <tr><td style="color:var(--muted)">İşletim Sistemi</td>
                <td style="color:var(--text)">${s.operating_system}</td></tr>
            <tr><td style="color:var(--muted)">Tarih</td>
                <td style="color:var(--red)">${new Date(s.date_compromised).toLocaleString('tr-TR')}</td></tr>
            <tr><td style="color:var(--muted)">Malware Yolu</td>
                <td style="color:var(--orange);font-size:11px;word-break:break-all">${s.malware_path}</td></tr>
            <tr><td style="color:var(--muted)">Antivirüs</td>
                <td>${s.antiviruses&&s.antiviruses.length>0
                  ? s.antiviruses.map(a=>`<span class="badge bd-blue" style="margin:1px">${a}</span>`).join('')
                  : '<span class="badge bd-red">Yok</span>'}</td></tr>
            <tr><td style="color:var(--muted)">Kurumsal Servis</td>
                <td style="color:var(--cyan)">${(s.total_corporate||0).toLocaleString()}</td></tr>
            <tr><td style="color:var(--muted)">Kullanıcı Servisi</td>
                <td style="color:var(--cyan)">${(s.total_user||0).toLocaleString()}</td></tr>
          </table>
        </div>`).join('')}` : ''}
  </div>

  <!-- HIBP -->
  <div class="card">
    <div class="card-hdr">
      <i class="fas fa-database" style="color:${hb.found?'var(--red)':'var(--green)'}"></i>
      <span>HIBP Public — Domain Eşleşme</span>
      ${hb.found
        ? `<span class="badge bd-red" style="margin-left:auto">🚨 ${hb.breach_count} Eşleşme</span>`
        : `<span class="badge bd-green" style="margin-left:auto">✅ Temiz</span>`}
    </div>
    ${hb.error ? `<div style="color:var(--yellow);font-size:12px">⚠ ${hb.error}</div>` : ''}
    <p style="font-size:11px;color:var(--muted);margin-bottom:8px">
      ${hb.total_in_db||0} breach veritabanında arandı
    </p>
    ${hb.breaches&&hb.breaches.length>0 ? `
      <table class="m-tbl">
        <thead><tr><th>Breach</th><th>Domain</th><th>Tarih</th><th>Etkilenen</th><th>Sızan Veriler</th></tr></thead>
        <tbody>
          ${hb.breaches.map(b=>`
            <tr>
              <td><strong>${b.name}</strong></td>
              <td style="color:var(--muted)">${b.domain}</td>
              <td style="color:var(--muted)">${b.date}</td>
              <td style="color:var(--cyan)">${(b.count||0).toLocaleString()}</td>
              <td>${(b.data_types||[]).map(d=>
                `<span class="badge bd-yellow" style="margin:1px;font-size:10px">${d}</span>`).join('')}</td>
            </tr>`).join('')}
        </tbody>
      </table>` : ''}
  </div>`;

  document.getElementById('br-res').innerHTML=html;
}

// ── PASSWORD ──
async function doPassword(){
  const pw=document.getElementById('pw-inp').value;
  if(!pw) return;
  show('pw-loader'); document.getElementById('pw-res').innerHTML='';
  const r=await api('/api/breach/password',{password:pw});
  hide('pw-loader');
  let html='';
  if(r.error){
    html=`<div class="badge bd-yellow">⚠ ${r.error}</div>`;
  } else if(r.pwned){
    incStat('breach');
    html=`
      <div style="text-align:center;padding:20px">
        <div style="font-size:48px;margin-bottom:12px">🚨</div>
        <div class="badge bd-red" style="font-size:16px;padding:8px 20px">
          Bu şifre ${r.count.toLocaleString()} kez sızdı!
        </div>
        <p style="color:var(--muted);font-size:12px;margin-top:12px">
          Bu şifreyi kullandığınız tüm hesaplarda hemen değiştirin.
        </p>
      </div>`;
  } else {
    html=`
      <div style="text-align:center;padding:20px">
        <div style="font-size:48px;margin-bottom:12px">✅</div>
        <div class="badge bd-green" style="font-size:14px;padding:8px 20px">
          Bu şifre sızıntı veritabanlarında görülmedi
        </div>
      </div>`;
  }
  document.getElementById('pw-res').innerHTML=html;
}

// ── EMAIL ──
async function doEmail(){
  const email=document.getElementById('em-inp').value.trim();
  if(!email) return;
  show('em-loader'); document.getElementById('em-res').innerHTML='';
  const r=await api('/api/email',{email});
  hide('em-loader');
  incStat('total'); addRecent('email',email);
  const b=(v,t)=>v?`<span class="badge bd-green">${t}</span>`:`<span class="badge bd-red">✗ ${t}</span>`;
  document.getElementById('em-res').innerHTML=`
  <div class="g2">
    <div class="card">
      <div class="card-hdr"><i class="fas fa-check-circle"></i><span>Doğrulama</span></div>
      <table class="m-tbl">
        <tr><td style="color:var(--muted)">Format</td><td>${b(r.format_valid,'Geçerli')}</td></tr>
        <tr><td style="color:var(--muted)">Domain</td><td>${b(r.domain_valid,'Aktif')}</td></tr>
        <tr><td style="color:var(--muted)">Geçici mi</td><td>${b(!r.disposable,'Hayır')}</td></tr>
        <tr><td style="color:var(--muted)">Ücretsiz</td>
          <td>${r.free_provider?'<span class="badge bd-yellow">Evet</span>':'<span class="badge bd-blue">Hayır</span>'}</td></tr>
        <tr><td style="color:var(--muted)">Gravatar</td><td>${b(r.gravatar?.exists,'Mevcut')}</td></tr>
      </table>
      ${r.gravatar?.exists?`<br><a href="${r.gravatar.url}" target="_blank" style="color:var(--cyan);font-size:12px">→ Gravatar Profili</a>`:''}
    </div>
    <div class="card">
      <div class="card-hdr"><i class="fas fa-server"></i><span>MX Kayıtları</span></div>
      ${(r.mx_records||[]).map(m=>`
        <div style="padding:5px 0;border-bottom:1px solid var(--border);font-size:12px;color:var(--cyan)">${m}</div>
      `).join('')||'<span style="color:var(--muted)">Kayıt bulunamadı</span>'}
      <br>
      <div class="card-hdr" style="margin-top:8px"><i class="fas fa-share-alt"></i><span>Sosyal Tahmin</span></div>
      ${Object.entries(r.social_guess||{}).map(([k,v])=>`
        <div style="padding:4px 0;font-size:12px">
          <span style="color:var(--muted);width:80px;display:inline-block">${k}</span>
          <a href="${v}" target="_blank" style="color:var(--cyan)">→ ${v}</a>
        </div>`).join('')}
    </div>
  </div>`;
}

// ── IP ──
async function doIP(){
  const ip=document.getElementById('ip-inp').value.trim();
  if(!ip) return;
  show('ip-loader'); document.getElementById('ip-res').innerHTML='';
  const r=await api('/api/ip',{ip});
  hide('ip-loader');
  incStat('total'); addRecent('ip',ip);
  const info=r.info||{};
  document.getElementById('ip-res').innerHTML=`
  <div class="g3" style="margin-bottom:16px">
    <div class="stat"><div class="num" style="font-size:20px">${info.country||'N/A'}</div><div class="lbl">Ülke</div></div>
    <div class="stat"><div class="num" style="font-size:20px">${info.city||'N/A'}</div><div class="lbl">Şehir</div></div>
    <div class="stat"><div class="num" style="font-size:14px">${r.asn?.asn||'N/A'}</div><div class="lbl">ASN</div></div>
  </div>
  <div class="g2">
    <div class="card">
      <div class="card-hdr"><i class="fas fa-info-circle"></i><span>Genel Bilgiler</span></div>
      <table class="m-tbl">
        ${[['IP',info.ip],['Hostname',info.hostname],['Şehir',info.city],
           ['Bölge',info.region],['Ülke',info.country],['Koordinat',info.location],
           ['Org',info.org],['Timezone',info.timezone]
          ].map(([k,v])=>`<tr>
            <td style="color:var(--muted)">${k}</td>
            <td style="color:var(--cyan)">${v||'N/A'}</td></tr>`).join('')}
      </table>
    </div>
    <div class="card">
      <div class="card-hdr"><i class="fas fa-ban" style="color:var(--red)"></i><span>Blacklist</span></div>
      ${Object.entries(r.blacklist||{}).map(([l,s])=>`
        <div style="display:flex;justify-content:space-between;padding:7px 0;
                    border-bottom:1px solid var(--border);font-size:12px">
          <span style="color:var(--muted)">${l}</span>
          <span class="badge ${s===false?'bd-green':s===true?'bd-red':'bd-yellow'}">
            ${s===false?'✅ Temiz':s===true?'🚨 Listede':'⚠ Hata'}
          </span>
        </div>`).join('')}
    </div>
  </div>`;
}

// ── DNS ──
async function doDNS(){
  const domain=document.getElementById('dns-inp').value.trim();
  if(!domain) return;
  show('dns-loader'); document.getElementById('dns-res').innerHTML='';
  const r=await api('/api/dns',{domain});
  hide('dns-loader');
  incStat('total'); addRecent('dns',domain);
  const w=r.whois||{};
  document.getElementById('dns-res').innerHTML=`
  <div class="g2">
    <div class="card">
      <div class="card-hdr"><i class="fas fa-list"></i><span>DNS Kayıtları</span></div>
      <table class="m-tbl">
        <thead><tr><th>Tip</th><th>Değer</th></tr></thead>
        <tbody>
        ${Object.entries(r.records||{}).map(([type,vals])=>
          (vals||[]).filter(v=>v).map(v=>`
          <tr><td><span class="badge bd-blue">${type}</span></td>
              <td style="font-size:11px;word-break:break-all">${v}</td></tr>`).join('')
        ).join('')}
        </tbody>
      </table>
    </div>
    <div class="card">
      <div class="card-hdr"><i class="fas fa-id-card"></i><span>WHOIS</span></div>
      <table class="m-tbl">
        ${[['Registrar',w.registrar],['Kayıt',w.creation_date],
           ['Bitiş',w.expiration_date],['Ülke',w.country],
           ['Email',Array.isArray(w.emails)?w.emails.join(', '):w.emails]
          ].map(([k,v])=>`<tr>
            <td style="color:var(--muted)">${k}</td>
            <td style="font-size:11px">${v||'N/A'}</td></tr>`).join('')}
      </table>
      <div style="font-size:11px;color:var(--muted);margin-top:8px">Name Servers:</div>
      ${(w.name_servers||[]).map(ns=>`
        <div style="font-size:11px;color:var(--cyan);padding:2px 0">${ns}</div>`).join('')}
    </div>
  </div>`;
}

// ── PORT ──
async function doPort(){
  const host=document.getElementById('pt-inp').value.trim();
  const range=document.getElementById('pt-range').value;
  if(!host) return;
  document.getElementById('pt-btn').disabled=true;
  show('pt-loader'); document.getElementById('pt-res').innerHTML='';
  const r=await api('/api/port',{host,range});
  hide('pt-loader');
  document.getElementById('pt-btn').disabled=false;
  if(r.open_ports?.length) incStat('open', r.open_ports.length);
  addRecent('port',host);
  document.getElementById('pt-res').innerHTML=`
  <div class="g3" style="margin-bottom:16px">
    <div class="stat"><div class="num" style="color:var(--green)">${r.open_ports?.length||0}</div><div class="lbl">Açık</div></div>
    <div class="stat"><div class="num" style="color:var(--red)">${r.closed_count||0}</div><div class="lbl">Kapalı</div></div>
    <div class="stat"><div class="num" style="font-size:14px">${r.scan_time||'N/A'}</div><div class="lbl">Süre</div></div>
  </div>
  <div class="card">
    <div class="card-hdr"><i class="fas fa-door-open" style="color:var(--green)"></i><span>Açık Portlar</span></div>
    ${!r.open_ports||r.open_ports.length===0
      ?'<div class="badge bd-green">✅ Açık port bulunamadı</div>'
      :`<table class="m-tbl">
        <thead><tr><th>Port</th><th>Servis</th><th>Durum</th><th>Banner</th></tr></thead>
        <tbody>${r.open_ports.map(p=>`<tr>
          <td><strong style="color:var(--yellow)">${p.port}</strong></td>
          <td><span class="badge bd-blue">${p.service}</span></td>
          <td><span class="badge bd-green">AÇIK</span></td>
          <td style="font-size:10px;color:var(--muted)">${p.banner||'N/A'}</td>
        </tr>`).join('')}</tbody></table>`}
  </div>`;
}

// ── REALTIME ──
function rtLog(msg,color='var(--text)'){
  const el=document.getElementById('rt-log');
  const t=new Date().toLocaleTimeString('tr-TR');
  el.innerHTML+=`<div style="color:${color};padding:1px 0">
    <span style="color:var(--muted)">[${t}]</span> ${msg}</div>`;
  el.scrollTop=el.scrollHeight;
}
function startRT(){
  const target=document.getElementById('rt-inp').value.trim();
  const type=document.getElementById('rt-type').value;
  if(!target) return;
  document.getElementById('rt-btn').style.display='none';
  document.getElementById('rt-stop').style.display='inline-block';
  document.getElementById('rt-log').innerHTML='';
  rtLog(`🚀 Hedef: <strong style="color:var(--cyan)">${target}</strong>`,'var(--cyan)');
  rtLog(`📡 Mod: ${type.toUpperCase()}`,'var(--blue)');
  socket.emit('realtime_scan',{target,type});
}
function stopRT(){
  document.getElementById('rt-btn').style.display='inline-block';
  document.getElementById('rt-stop').style.display='none';
  rtLog('⛔ Durduruldu','var(--red)');
}
socket.on('scan_start',d=>rtLog(`▶ ${d.message}`,'var(--green)'));
socket.on('scan_result',d=>{
  rtLog(`✅ Sonuç — ${d.type.toUpperCase()}`,'var(--green)');
  document.getElementById('rt-res').innerHTML=`
  <div class="card">
    <div class="card-hdr"><i class="fas fa-chart-line"></i><span>Sonuç</span></div>
    <pre style="color:var(--green);font-size:11px;white-space:pre-wrap;
                background:var(--bg0);padding:14px;border-radius:6px">
${JSON.stringify(d.data,null,2)}</pre>
  </div>`;
});
socket.on('scan_complete',d=>{
  rtLog(`🏁 ${d.message}`,'var(--yellow)');
  document.getElementById('rt-btn').style.display='inline-block';
  document.getElementById('rt-stop').style.display='none';
});
socket.on('connect',()=>rtLog('🔌 WebSocket bağlandı','var(--cyan)'));
socket.on('disconnect',()=>rtLog('🔴 Bağlantı kesildi','var(--red)'));

// ── ENTER ──
const enterMap={
  'q-inp':quickScan,'ip-inp':doIP,'dns-inp':doDNS,
  'pt-inp':doPort,'em-inp':doEmail,'br-email':doBreachFull,
  'pw-inp':doPassword,
};
Object.entries(enterMap).forEach(([id,fn])=>{
  const el=document.getElementById(id);
  if(el) el.addEventListener('keypress',e=>{if(e.key==='Enter')fn();});
});
</script>
</body>
</html>"""

# ══════════════════════════════════════════
#              FLASK
# ══════════════════════════════════════════

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mosint-alpha-2024'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*',
                    logger=False, engineio_logger=False)

@app.route('/')
def index():
    return render_template_string(HTML, version=VERSION)

# ── Breach ──
@app.route('/api/breach/full', methods=['POST'])
def api_breach_full():
    d = request.get_json()
    return jsonify(breach_full(d.get('email','')))

@app.route('/api/breach/password', methods=['POST'])
def api_breach_password():
    d = request.get_json()
    return jsonify(breach_password(d.get('password','')))

# ── Diğerleri ──
@app.route('/api/ip', methods=['POST'])
def api_ip():
    d = request.get_json()
    return jsonify(ip_lookup(d.get('ip','')))

@app.route('/api/dns', methods=['POST'])
def api_dns():
    d = request.get_json()
    return jsonify(dns_lookup(d.get('domain','')))

@app.route('/api/port', methods=['POST'])
def api_port():
    d = request.get_json()
    return jsonify(port_scan(d.get('host',''), d.get('range','common')))

@app.route('/api/email', methods=['POST'])
def api_email():
    d = request.get_json()
    return jsonify(email_check(d.get('email','')))

# ── WebSocket ──
@socketio.on('realtime_scan')
def handle_realtime(data):
    target = data.get('target','')
    stype  = data.get('type','ip')
    emit('scan_start', {'message': f'Tarama → {target}'})

    def run():
        if   stype == 'ip':     res = ip_lookup(target)
        elif stype == 'port':   res = port_scan(target, 'common')
        elif stype == 'dns':    res = dns_lookup(target)
        elif stype == 'email':  res = email_check(target)
        elif stype == 'breach': res = breach_full(target)
        else:                   res = {}
        socketio.emit('scan_result',   {'type': stype, 'data': res})
        socketio.emit('scan_complete', {'message': 'Tamamlandı ✔'})

    threading.Thread(target=run, daemon=True).start()

# ══════════════════════════════════════════
#              BAŞLAT
# ══════════════════════════════════════════

if __name__ == '__main__':
    startup_animation()
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG)