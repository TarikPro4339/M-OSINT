@echo off
REM ======================================================================
REM   M-OSINT Baslatici
REM   Surum   : v0.0.3 (Alpha)
REM   Yapimci : tarikpro43391
REM
REM   Bu dosya; Python kontrolu, bagimlilik kurulumu ve uygulamanin
REM   baslatilmasini tek bir yerden, okunakli ve guvenli bicimde yapar.
REM ======================================================================

chcp 65001 >nul
title M-OSINT v0.0.3 (Alpha) - by tarikpro43391
setlocal enabledelayedexpansion

REM --- Ayarlar ------------------------------------------------------------
set "APP_PORT=5000"
set "APP_URL=http://127.0.0.1:%APP_PORT%"
set "MIN_PY_MAJOR=3"
set "MIN_PY_MINOR=9"
set "MAX_PY_MINOR=12"
set "USE_VENV=1"
set "VENV_DIR=.venv"
set "LOG_FILE=mosint_kurulum.log"

REM --- Calisma dizinini bu dosyanin bulundugu klasore sabitle -------------
cd /d "%~dp0"

call :BANNER
call :STEP_INTRO

call :CHECK_PYTHON
if errorlevel 1 goto :FAIL

call :CHECK_PIP
if errorlevel 1 goto :FAIL

if "%USE_VENV%"=="1" (
    call :SETUP_VENV
    if errorlevel 1 goto :FAIL
)

call :INSTALL_REQUIREMENTS
if errorlevel 1 goto :FAIL

call :LAUNCH_APP
goto :END

REM ======================================================================
REM   FONKSIYONLAR
REM ======================================================================

:BANNER
REM --- Havali, renk gecisli acilis ekrani -------------------------------
cls
set "frames=0A 0B 0D 0E 0F 0B"
for %%c in (%frames%) do (
    color %%c
    cls
    echo.
    echo   ███╗   ███╗       ██████╗ ███████╗██╗███╗   ██╗████████╗
    echo   ████╗ ████║      ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
    echo   ██╔████╔██║█████╗██║   ██║███████╗██║██╔██╗ ██║   ██║
    echo   ██║╚██╔╝██║╚════╝██║   ██║╚════██║██║██║╚██╗██║   ██║
    echo   ██║ ╚═╝ ██║      ╚██████╔╝███████║██║██║ ╚████║   ██║
    echo   ╚═╝     ╚═╝       ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
    echo.
    ping -n 1 -w 90 127.0.0.1 >nul
)
color 0B
cls
echo.
echo   ============================================================
echo         M - O S I N T   v0.0.3 ^(Alpha^)
echo         OSINT Bilgi Toplama Paneli
echo         Yapimci : tarikpro43391
echo   ============================================================
echo.
exit /b 0

:STEP_INTRO
echo   [*] Sistem kontrolleri baslatiliyor, lutfen bekleyin...
call :PROGRESS_BAR
echo.
exit /b 0

:PROGRESS_BAR
<nul set /p "=  ["
for /l %%i in (1,1,30) do (
    <nul set /p "=#"
    ping -n 1 -w 25 127.0.0.1 >nul
)
echo ] Tamam
exit /b 0

:CHECK_PYTHON
echo   [1/4] Python kontrol ediliyor...
where python >nul 2>nul
if errorlevel 1 (
    echo   [HATA] Python bulunamadi.
    echo          Lutfen Python %MIN_PY_MAJOR%.%MIN_PY_MINOR% - %MIN_PY_MAJOR%.%MAX_PY_MINOR% surumunu kurun:
    echo          https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "PYMAJOR=%%a"
    set "PYMINOR=%%b"
)

echo   [OK]  Python bulundu: %PYVER%

if not "%PYMAJOR%"=="%MIN_PY_MAJOR%" (
    echo   [UYARI] Beklenmeyen Python surumu ^(%PYVER%^). Sorun yasarsaniz
    echo           Python %MIN_PY_MAJOR%.%MIN_PY_MINOR%-%MIN_PY_MAJOR%.%MAX_PY_MINOR% kullanmayi deneyin.
) else if %PYMINOR% LSS %MIN_PY_MINOR% (
    echo   [UYARI] Python surumunuz eski olabilir. Onerilen: %MIN_PY_MAJOR%.%MIN_PY_MINOR%+
) else if %PYMINOR% GTR %MAX_PY_MINOR% (
    echo   [UYARI] Python surumunuz test edilenden yeni olabilir. Onerilen: 3.%MIN_PY_MINOR%-3.%MAX_PY_MINOR%
)
echo.
exit /b 0

:CHECK_PIP
echo   [2/4] pip kontrol ediliyor...
python -m pip --version >nul 2>nul
if errorlevel 1 (
    echo   [HATA] pip bulunamadi. Python kurulumunuzu onarin ^(pip modulu eksik^).
    exit /b 1
)
echo   [OK]  pip hazir.
echo.
exit /b 0

:SETUP_VENV
echo   [3/4] Sanal ortam ^(venv^) hazirlaniyor...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo         Ilk calistirma: "%VENV_DIR%" olusturuluyor...
    python -m venv "%VENV_DIR%" >>"%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo   [UYARI] Sanal ortam olusturulamadi, sistem Python'u kullanilacak.
        set "USE_VENV=0"
        exit /b 0
    )
)
call "%VENV_DIR%\Scripts\activate.bat"
echo   [OK]  Sanal ortam aktif: %VENV_DIR%
echo.
exit /b 0

:INSTALL_REQUIREMENTS
echo   [4/4] Bagimliliklar kontrol ediliyor...
if not exist requirements.txt (
    echo   [UYARI] requirements.txt bulunamadi, bu adim atlaniyor.
    echo           Gerekli paketleri elle kurmaniz gerekebilir:
    echo           flask, flask-socketio, requests, dnspython, python-whois, eventlet
    echo.
    exit /b 0
)

echo         ^(flask, flask-socketio, requests, dnspython, python-whois, eventlet^)
python -m pip install --upgrade pip --quiet --disable-pip-version-check >>"%LOG_FILE%" 2>&1
python -m pip install -r requirements.txt --quiet --disable-pip-version-check >>"%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo   [UYARI] Sessiz kurulum basarisiz oldu, ayrintili modda tekrar deneniyor...
    python -m pip install -r requirements.txt --disable-pip-version-check
    if errorlevel 1 (
        echo   [HATA] Bagimliliklar kurulamadi. Ayrintilar icin "%LOG_FILE%" dosyasina bakin.
        exit /b 1
    )
)

echo   [OK]  Bagimliliklar hazir.
echo.
exit /b 0

:LAUNCH_APP
echo   ============================================================
echo   [*] M-OSINT baslatiliyor... Panel: %APP_URL%
echo   [*] Tarayici birkac saniye icinde otomatik acilacak.
echo   [*] Kapatmak icin bu pencereyi kapatin veya CTRL+C basin.
echo   ============================================================
echo.

start "" /b cmd /c "ping -n 4 127.0.0.1 >nul & start "" "%APP_URL%""

if exist mosint_v003.py (
    python mosint_v003.py
) else if exist mosint.py (
    python mosint.py
) else (
    echo   [HATA] mosint_v003.py / mosint.py bulunamadi.
    echo          Bu .bat dosyasini uygulamanin ana klasorune koyun.
    goto :FAIL
)

echo.
echo   [i] M-OSINT kapatildi.
goto :END

:FAIL
echo.
echo   ------------------------------------------------------------
echo   Kurulum ya da baslatma sirasinda bir hata olustu.
echo   Ayrintilar icin varsa "%LOG_FILE%" dosyasini kontrol edin.
echo   ------------------------------------------------------------
color 0C
pause
exit /b 1

:END
color 0B
echo.
pause
exit /b 0
