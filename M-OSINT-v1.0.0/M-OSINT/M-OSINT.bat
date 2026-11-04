@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title M-OSINT - Local Intelligence Workbench
color 0A
echo.
echo  M-OSINT // LOCAL INTELLIGENCE WORKBENCH
echo  Core: no pip packages, no admin rights required.
echo.
if not exist "run.py" goto :missing
if exist ".venv\Scripts\python.exe" goto :venv
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto :py
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto :python
echo [ERROR] Install Python 3.10 or newer from https://www.python.org/downloads/
echo Enable Add Python to PATH. Then run this file again.
pause
exit /b 1
:venv
".venv\Scripts\python.exe" run.py %*
goto :done
:py
py -3 run.py %*
goto :done
:python
python run.py %*
goto :done
:missing
echo [ERROR] Extract the entire ZIP before launching M-OSINT.bat.
pause
exit /b 1
:done
if errorlevel 1 (
 echo [ERROR] Startup stopped. Read the message above.
 pause
 exit /b 1
)
endlocal
