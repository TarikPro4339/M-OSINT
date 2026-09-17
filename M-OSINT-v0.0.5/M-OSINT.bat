@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem M-OSINT v0.0.5 - ASCII-only Windows launcher
rem This file intentionally uses ASCII only for cmd.exe compatibility.

chcp 65001 >nul
title M-OSINT v0.0.5 - Local Launcher
color 0B

set "APP_NAME=M-OSINT"
set "APP_VERSION=v0.0.5 Alpha"
set "APP_FILE=mosint_v005.py"
set "HOST=127.0.0.1"
set "PORT=5000"
set "APP_URL=http://%HOST%:%PORT%"
set "VENV_DIR=.venv"
set "REQ_FILE=requirements.txt"
set "LOG_FILE=mosint_launcher.log"
set "SYSTEM_PYTHON=python"

cd /d "%~dp0"

call :HEADER
call :CHECK_FILES || goto :FAIL
call :FIND_PYTHON || goto :FAIL
call :CHECK_VERSION || goto :FAIL
call :CREATE_VENV || goto :FAIL
call :INSTALL_DEPS || goto :FAIL
call :CHECK_PORT || goto :END
call :OPEN_BROWSER
call :RUN
goto :END

:HEADER
cls
echo.
echo  +----------------------------------------------------------+
echo  ^|                 M - O S I N T                          ^|
echo  ^|                 %APP_VERSION%                           ^|
echo  +----------------------------------------------------------+
echo  Local OSINT panel: %APP_URL%
echo.
exit /b 0

:INFO
echo  [*] %~1
exit /b 0

:OK
echo  [OK] %~1
exit /b 0

:ERROR
color 0C
echo  [ERROR] %~1
color 0B
exit /b 0

:CHECK_FILES
call :INFO "Checking project files..."
if not exist "%APP_FILE%" (
  call :ERROR "%APP_FILE% was not found. Run this file from the project folder."
  exit /b 1
)
if not exist "%REQ_FILE%" (
  call :ERROR "%REQ_FILE% was not found."
  exit /b 1
)
call :OK "Project files found."
exit /b 0

:FIND_PYTHON
call :INFO "Checking Python..."
python --version >nul 2>nul
if not errorlevel 1 (
  set "SYSTEM_PYTHON=python"
  call :OK "Using the Python command."
  exit /b 0
)
py -3 --version >nul 2>nul
if not errorlevel 1 (
  set "SYSTEM_PYTHON=py -3"
  call :OK "Using the Python Launcher."
  exit /b 0
)
call :ERROR "Python 3.9+ could not be started. Install Python from python.org and enable PATH."
echo  https://www.python.org/downloads/
exit /b 1

:CHECK_VERSION
for /f "tokens=2 delims= " %%V in ('%SYSTEM_PYTHON% --version 2^>^&1') do set "PYVER=%%V"
for /f "tokens=1,2 delims=." %%A in ("%PYVER%") do (
  set "PY_MAJOR=%%A"
  set "PY_MINOR=%%B"
)
if not "%PY_MAJOR%"=="3" (
  call :ERROR "Python 3 is required. Detected: %PYVER%"
  exit /b 1
)
if %PY_MINOR% LSS 9 (
  call :ERROR "Python 3.9 or newer is required. Detected: %PYVER%"
  exit /b 1
)
call :OK "Using Python %PYVER%."
exit /b 0

:CREATE_VENV
call :INFO "Preparing virtual environment..."
if not exist "%VENV_DIR%\Scripts\python.exe" (
  %SYSTEM_PYTHON% -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :ERROR "Could not create the virtual environment. See %LOG_FILE%."
    exit /b 1
  )
)
set "PYTHON=%CD%\%VENV_DIR%\Scripts\python.exe"
call :OK "Virtual environment is ready."
exit /b 0

:INSTALL_DEPS
call :INFO "Checking dependencies..."
"%PYTHON%" -c "import flask, flask_socketio, requests, dns, whois, eventlet" >nul 2>nul
if not errorlevel 1 (
  call :OK "Dependencies are ready."
  exit /b 0
)
echo  Installing missing dependencies. This may take a moment...
"%PYTHON%" -m pip install -r "%REQ_FILE%" --disable-pip-version-check >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :ERROR "Dependency installation failed. See %LOG_FILE%."
  exit /b 1
)
call :OK "Dependencies installed."
exit /b 0

:CHECK_PORT
call :INFO "Checking local port %PORT%..."
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo.
  echo  [INFO] A service is already running at %APP_URL%
  choice /C AE /N /M "Open it in browser or exit? [A/E]"
  if errorlevel 2 exit /b 1
  start "" "%APP_URL%"
  exit /b 1
)
call :OK "Port %PORT% is available."
exit /b 0

:OPEN_BROWSER
call :INFO "Starting panel. Browser will open shortly..."
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process '%APP_URL%'"
exit /b 0

:RUN
echo.
echo  +----------------------------------------------------------+
echo  Panel: %APP_URL%
echo  Stop the server with CTRL+C.
echo  +----------------------------------------------------------+
echo.
"%PYTHON%" "%APP_FILE%"
exit /b %errorlevel%

:FAIL
echo.
echo  Startup failed. Check "%LOG_FILE%" for details.
echo.
pause
exit /b 1

:END
echo.
echo  M-OSINT has stopped.
pause
endlocal
exit /b 0
