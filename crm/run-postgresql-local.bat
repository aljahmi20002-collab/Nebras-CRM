@echo off
rem Run NebrasCRM against a native/local PostgreSQL service on Windows (no Docker).
rem Configuration is read from .env.postgresql.local.bat by default.

setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "CONFIG_FILE=%POSTGRESQL_LOCAL_CONFIG%"
if not defined CONFIG_FILE set "CONFIG_FILE=%CD%\.env.postgresql.local.bat"

if not exist "%CONFIG_FILE%" (
  echo.
  echo [ERROR] Native PostgreSQL configuration was not found:
  echo         %CONFIG_FILE%
  echo.
  echo Create it with:
  echo   copy .env.postgresql.local.bat.example .env.postgresql.local.bat
  echo Then edit the password to match your PostgreSQL user.
  exit /b 1
)

call "%CONFIG_FILE%"
if errorlevel 1 (
  echo [ERROR] Could not load the local PostgreSQL configuration file.
  exit /b 1
)

if /I not "%CRM_DB_ENGINE%"=="postgresql" if /I not "%CRM_DB_ENGINE%"=="postgres" (
  echo [ERROR] CRM_DB_ENGINE must be postgresql in %CONFIG_FILE%.
  exit /b 1
)

call "%~dp0run.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
