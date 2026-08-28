@echo off
rem Run NebrasCRM against a native/local MariaDB service on Windows (no Docker).
rem Configuration is read from .env.mariadb.local.bat by default.

setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "CONFIG_FILE=%MARIADB_LOCAL_CONFIG%"
if not defined CONFIG_FILE set "CONFIG_FILE=%CD%\.env.mariadb.local.bat"

if not exist "%CONFIG_FILE%" (
  copy /y .env.mariadb.local.bat.example .env.mariadb.local.bat >nul
  echo [INFO] Created .env.mariadb.local.bat.
  echo [INFO] Edit CRM_DB_PASSWORD to match your MariaDB user, then run this file again.
  exit /b 1
)

call "%CONFIG_FILE%"
if errorlevel 1 (
  echo [ERROR] Could not load the local MariaDB configuration file.
  exit /b 1
)

if /I not "%CRM_DB_ENGINE%"=="mariadb" (
  echo [ERROR] CRM_DB_ENGINE must be mariadb in %CONFIG_FILE%.
  exit /b 1
)

rem Try common native service names. This is harmless when the service is already running.
for %%S in (MariaDB MySQL MySQL80) do (
  sc query "%%S" >nul 2>nul && net start "%%S" >nul 2>nul
)

call "%~dp0run.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
