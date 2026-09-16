@echo off
chcp 65001 >nul
color 0B
cls

echo.
echo  ╔══════════════════════════════════════════════════════════════════╗
echo  ║                                                                  ║
echo  ║   ███╗   ███╗      ██████╗ ███████╗██╗███╗   ██╗████████╗        ║
echo  ║   ████╗ ████║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝        ║
echo  ║   ██╔████╔██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║           ║
echo  ║   ██║╚██╔╝██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║           ║
echo  ║   ██║ ╚═╝ ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║           ║
echo  ║   ╚═╝     ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝           ║
echo  ║                                                                  ║
echo  ║                  v0.0.1 (Alpha) - OSINT Framework                ║
echo  ║                     [ Sadece Egitim Amacli ]                     ║
echo  ╚══════════════════════════════════════════════════════════════════╝
echo.

:: Renk ayarla
color 0B

echo  [*] Sistem baslatiliyor...
echo.
timeout /t 1 /nobreak >nul

:: ──────────────────────────────
:: PYTHON KONTROL
:: ──────────────────────────────
echo  [*] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] HATA: Python bulunamadi!
    echo  [!] Lutfen Python 3.8 veya uzeri yukleyin.
    echo  [!] Indirme: https://python.org/downloads
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [+] %PYVER% bulundu.
echo.

:: ──────────────────────────────
:: PIP KONTROL
:: ──────────────────────────────
echo  [*] pip kontrol ediliyor...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] pip bulunamadi! Python kurulumunu kontrol edin.
    pause
    exit /b 1
)
echo  [+] pip hazir.
echo.

:: ──────────────────────────────
:: BAGIMLILIKLAR
:: ──────────────────────────────
echo  [*] Bagimliliklar kontrol ediliyor...
echo  ─────────────────────────────────────────
echo.

:: Flask
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo  [+] Yukleniyor: flask
    pip install flask -q --disable-pip-version-check
    if %errorlevel% equ 0 (echo  [OK] flask yuklendi.) else (echo  [!!] flask yuklenemedi!)
) else (
    echo  [OK] flask - mevcut
)

:: Flask-SocketIO
pip show flask-socketio >nul 2>&1
if %errorlevel% neq 0 (
    echo  [+] Yukleniyor: flask-socketio
    pip install flask-socketio -q --disable-pip-version-check
    if %errorlevel% equ 0 (echo  [OK] flask-socketio yuklendi.) else (echo  [!!] flask-socketio yuklenemedi!)
) else (
    echo  [OK] flask-socketio - mevcut
)

:: requests
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo  [+] Yukleniyor: requests
    pip install requests -q --disable-pip-version-check
    if %errorlevel% equ 0 (echo  [OK] requests yuklendi.) else (echo  [!!] requests yuklenemedi!)
) else (
    echo  [OK] requests - mevcut
)

:: dnspython
pip show dnspython >nul 2>&1
if %errorlevel% neq 0 (
    echo  [+] Yukleniyor: dnspython
    pip install dnspython -q --disable-pip-version-check
    if %errorlevel% equ 0 (echo  [OK] dnspython yuklendi.) else (echo  [!!] dnspython yuklenemedi!)
) else (
    echo  [OK] dnspython - mevcut
)

:: python-whois
pip show python-whois >nul 2>&1
if %errorlevel% neq 0 (
    echo  [+] Yukleniyor: python-whois
    pip install python-whois -q --disable-pip-version-check
    if %errorlevel% equ 0 (echo  [OK] python-whois yuklendi.) else (echo  [!!] python-whois yuklenemedi!)
) else (
    echo  [OK] python-whois - mevcut
)

:: eventlet
pip show eventlet >nul 2>&1
if %errorlevel% neq 0 (
    echo  [+] Yukleniyor: eventlet
    pip install eventlet -q --disable-pip-version-check
    if %errorlevel% equ 0 (echo  [OK] eventlet yuklendi.) else (echo  [!!] eventlet yuklenemedi!)
) else (
    echo  [OK] eventlet - mevcut
)

echo.
echo  ─────────────────────────────────────────
echo  [+] Tum bagimliliklar hazir!
echo.
timeout /t 1 /nobreak >nul

:: ──────────────────────────────
:: MOSINT.PY KONTROL
:: ──────────────────────────────
echo  [*] mosint.py kontrol ediliyor...
if not exist "%~dp0mosint.py" (
    echo.
    echo  [!] HATA: mosint.py bulunamadi!
    echo  [!] mosint.py dosyasinin bu bat dosyasiyla
    echo  [!] ayni klasorde olmasi gerekiyor.
    echo.
    echo  Klasor: %~dp0
    echo.
    pause
    exit /b 1
)
echo  [+] mosint.py bulundu.
echo.

:: ──────────────────────────────
:: TARAYICI AC
:: ──────────────────────────────
echo  [*] Panel adresi: http://127.0.0.1:5000
echo  [*] Tarayici 3 saniye sonra acilacak...
echo.

:: Arka planda tarayici ac (3 sn gecikme ile)
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:5000"

:: ──────────────────────────────
:: UYGULAMAYI BASLAT
:: ──────────────────────────────
echo  ════════════════════════════════════════════
echo   M-OSINT baslatiliyor...
echo   Durdurmak icin: CTRL + C
echo  ════════════════════════════════════════════
echo.

python "%~dp0mosint.py"

:: ──────────────────────────────
:: KAPANIŞ
:: ──────────────────────────────
echo.
echo  ════════════════════════════════════════════
echo   M-OSINT kapatildi.
echo  ════════════════════════════════════════════
echo.
pause