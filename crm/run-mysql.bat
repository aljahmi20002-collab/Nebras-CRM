@echo off
rem One-click NebrasCRM launcher for a local MySQL or MariaDB server on Windows.
rem Configuration is read from .env.mysql.local.bat by default.

setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "CONFIG_FILE=%MYSQL_LOCAL_CONFIG%"
if not defined CONFIG_FILE set "CONFIG_FILE=%CD%\.env.mysql.local.bat"
if not exist "%CONFIG_FILE%" if exist "%CD%\.env.mariadb.local.bat" set "CONFIG_FILE=%CD%\.env.mariadb.local.bat"

if not exist "%CONFIG_FILE%" (
  copy /y .env.mysql.local.bat.example .env.mysql.local.bat >nul
  echo [INFO] Created .env.mysql.local.bat.
  echo [INFO] Edit CRM_DB_PASSWORD to match your MySQL user, then run this file again.
  exit /b 1
)

call "%CONFIG_FILE%"
if errorlevel 1 (
  echo [ERROR] Could not load the local MySQL configuration file.
  exit /b 1
)

if /I "%CRM_DB_ENGINE%"=="mysql" goto :config_ok
if /I "%CRM_DB_ENGINE%"=="mariadb" goto :config_ok
echo [ERROR] CRM_DB_ENGINE must be mysql or mariadb in %CONFIG_FILE%.
exit /b 1

:config_ok
rem Try common native service names. This is harmless when the service is already running.
for %%S in (MySQL80 MySQL MariaDB) do (
  sc query "%%S" >nul 2>nul && net start "%%S" >nul 2>nul
)

call "%~dp0run.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
