@echo off
chcp 65001 >nul
color 0B
cls

echo.
echo  ╔═══════════════════════════════════════════════════════════════════╗
echo  ║                                                                   ║
echo  ║   ███╗   ███╗      ██████╗ ███████╗██╗███╗   ██╗████████╗         ║
echo  ║   ████╗ ████║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝         ║
echo  ║   ██╔████╔██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║            ║
echo  ║   ██║╚██╔╝██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║            ║
echo  ║   ██║ ╚═╝ ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║            ║
echo  ║   ╚═╝     ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝            ║
echo  ║                                                                   ║
echo  ║              v0.0.2  —  by tarikpro43391                          ║
echo  ║              Sadece Egitim Amaclidir                              ║
echo  ╚═══════════════════════════════════════════════════════════════════╝
echo.

timeout /t 1 /nobreak >nul

:: ── PYTHON ──
echo  [*] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] HATA: Python bulunamadi!
    echo  [!] https://python.org/downloads adresinden indirin.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PV=%%v
echo  [+] %PV% bulundu.
echo.

:: ── PIP ──
echo  [*] pip kontrol ediliyor...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] pip bulunamadi!
    pause
    exit /b 1
)
echo  [+] pip hazir.
echo.

:: ── BAGIMLILIKLAR ──
echo  [*] Bagimliliklar kontrol ediliyor...
echo  ─────────────────────────────────────────────

set PKGS=flask flask-socketio requests dnspython python-whois eventlet

for %%p in (%PKGS%) do (
    pip show %%p >nul 2>&1
    if errorlevel 1 (
        echo  [+] Yukleniyor : %%p
        pip install %%p -q --disable-pip-version-check
        if errorlevel 1 (
            echo  [!] HATA     : %%p yuklenemedi!
        ) else (
            echo  [OK] Yuklendi : %%p
        )
    ) else (
        echo  [OK] Mevcut   : %%p
    )
)

echo  ─────────────────────────────────────────────
echo  [+] Tum bagimliliklar hazir!
echo.

:: ── DOSYA KONTROL ──
if not exist "%~dp0mosint.py" (
    echo  [!] HATA: mosint.py bulunamadi!
    echo  [!] start.bat ile mosint.py ayni klasorde olmali.
    echo.
    pause
    exit /b 1
)
echo  [+] mosint.py bulundu.
echo.

:: ── TARAYICI ──
echo  [*] Panel  : http://127.0.0.1:5000
echo  [*] Tarayici 3 saniye sonra acilacak...
echo.
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:5000"

:: ── BASLAT ──
echo  ═════════════════════════════════════════════
echo   M-OSINT v0.0.2 baslatiliyor...
echo   Durdurmak icin CTRL + C
echo  ═════════════════════════════════════════════
echo.

python "%~dp0mosint.py"

echo.
echo  ═════════════════════════════════════════════
echo   M-OSINT kapatildi.
echo  ═════════════════════════════════════════════
echo.
pause