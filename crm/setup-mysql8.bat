@echo off
rem Prepare the complete Docker-based NebrasCRM + MySQL 8.4 stack.
rem Usage: setup-mysql8.bat [--reset-data]
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

where python3 >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python3 is required to run the MySQL 8 setup helper.
  exit /b 1
)

python3 "%~dp0setup_mysql8.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
