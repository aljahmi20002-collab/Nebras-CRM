@echo off
rem NebrasCRM Windows launcher
rem Usage: run.bat [port]
rem Examples:
rem   run.bat
rem   run.bat 9000
rem   set CRM_DB_ENGINE=mariadb && run.bat
rem   set CRM_DB_ENGINE=postgresql && run.bat
rem   set SEED_DEMO=1 && set CRM_DB_ENGINE=mariadb && run.bat

setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

if /I "%~1"=="--help" goto :help
if not "%~1"=="" set "PORT=%~1"
if not defined PORT set "PORT=8008"
if not defined CRM_DB_HOST set "CRM_DB_HOST=127.0.0.1"
if not defined CRM_DB_NAME set "CRM_DB_NAME=nebrascrm"

set "PYTHON="
if defined PYTHON_BIN (
  if exist "%PYTHON_BIN%" set "PYTHON=%PYTHON_BIN%"
)
if not defined PYTHON if exist ".venv\Scripts\python3.exe" set "PYTHON=%CD%\.venv\Scripts\python3.exe"
if not defined PYTHON (
  for %%P in (python3.exe python3 py.exe py) do (
    where %%P >nul 2>nul && (
      set "PYTHON=%%P"
      goto :python_found
    )
  )
) else goto :python_found

:python_found
if not defined PYTHON (
  echo.
  echo [ERROR] Python 3.10 or newer was not found.
  echo Install Python from https://www.python.org/downloads/ and enable "Add Python to PATH".
  echo You can also set PYTHON_BIN to the full path of python3.exe.
  exit /b 1
)

"%PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] NebrasCRM requires Python 3.10 or newer.
  "%PYTHON%" --version
  exit /b 1
)

"%PYTHON%" -c "import fastapi, uvicorn, multipart" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Installing Python requirements...
  "%PYTHON%" -m pip install -r requirements.txt
  if errorlevel 1 goto :pip_failed
)

"%PYTHON%" -c "import sys; p=int(sys.argv[1]); raise SystemExit(0 if 1 <= p <= 65535 else 1)" "%PORT%" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] PORT must be a number between 1 and 65535. Current value: %PORT%
  exit /b 1
)

if /I "%CRM_DB_ENGINE%"=="" set "CRM_DB_ENGINE=sqlite"
if /I "%CRM_DB_ENGINE%"=="mysql" set "CRM_DB_ENGINE=mariadb"
if /I "%CRM_DB_ENGINE%"=="postgres" set "CRM_DB_ENGINE=postgresql"
if /I "%CRM_DB_ENGINE%"=="postgresql" (
  if not defined CRM_DB_PORT set "CRM_DB_PORT=5432"
) else (
  if not defined CRM_DB_PORT set "CRM_DB_PORT=3306"
)
if /I "%CRM_DB_ENGINE%"=="sqlite" goto :sqlite
if /I "%CRM_DB_ENGINE%"=="mariadb" goto :mariadb
if /I "%CRM_DB_ENGINE%"=="postgresql" goto :postgresql

echo [ERROR] CRM_DB_ENGINE must be sqlite, mariadb/mysql, or postgresql.
exit /b 1

:sqlite
set "DB_FILE="
for /f "usebackq delims=" %%D in (`"%PYTHON%" -c "import db; print(db.DB_PATH)"`) do set "DB_FILE=%%D"
if not defined DB_FILE (
  echo [ERROR] Could not determine the SQLite database path.
  exit /b 1
)
if not exist "%DB_FILE%" (
  echo [INFO] Creating SQLite database and demo data...
  call :seed_demo
  if errorlevel 1 exit /b 1
)
goto :start

:mariadb
"%PYTHON%" -c "import pymysql" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Installing PyMySQL for MySQL/MariaDB support...
  "%PYTHON%" -m pip install "PyMySQL>=1.1.0"
  if errorlevel 1 goto :pip_failed
)
echo [INFO] MySQL/MariaDB mode: %CRM_DB_HOST%:%CRM_DB_PORT%/%CRM_DB_NAME%
"%PYTHON%" -c "import db; connection=db.connect(); connection.close()" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Could not connect to the configured MySQL/MariaDB server.
  echo Check CRM_DB_HOST, CRM_DB_PORT, CRM_DB_NAME, CRM_DB_USER and CRM_DB_PASSWORD.
  echo For one-click local MySQL/MariaDB startup, use: run-mysql.bat
  echo To use local SQLite instead: set CRM_DB_ENGINE=sqlite ^&^& run.bat
  exit /b 1
)
echo [INFO] MySQL/MariaDB connection verified. Tables are created automatically when the server starts.
if "%SEED_DEMO%"=="1" (
  echo [INFO] Loading demo data into MySQL/MariaDB...
  call :seed_demo
  if errorlevel 1 exit /b 1
)
goto :start

:postgresql
"%PYTHON%" -c "import psycopg" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Installing Psycopg for PostgreSQL support...
  "%PYTHON%" -m pip install "psycopg[binary]>=3.2.0"
  if errorlevel 1 goto :pip_failed
)
echo [INFO] PostgreSQL mode: %CRM_DB_HOST%:%CRM_DB_PORT%/%CRM_DB_NAME%
"%PYTHON%" -c "import db; connection=db.connect(); connection.close()" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Could not connect to the configured PostgreSQL server.
  echo Check CRM_DB_HOST, CRM_DB_PORT, CRM_DB_NAME, CRM_DB_USER, CRM_DB_PASSWORD and CRM_DB_SSLMODE.
  echo For native local PostgreSQL configuration, use: run-postgresql-local.bat
  echo To use local SQLite instead: set CRM_DB_ENGINE=sqlite ^&^& run.bat
  exit /b 1
)
echo [INFO] PostgreSQL connection verified. Tables are created automatically when the server starts.
if "%SEED_DEMO%"=="1" (
  echo [INFO] Loading demo data into PostgreSQL...
  call :seed_demo
  if errorlevel 1 exit /b 1
)
goto :start

:seed_demo
for %%S in (seed.py seed_intel.py seed_extra.py seed_geo.py seed_portal.py) do (
  if exist "%%S" (
    echo [INFO] Running %%S...
    "%PYTHON%" "%%S"
    if errorlevel 1 exit /b 1
  )
)
exit /b 0

:start
echo.
echo [INFO] NebrasCRM is running at http://localhost:%PORT%
echo [INFO] Open http://localhost:%PORT%/app in your browser.
echo [INFO] Press Ctrl+C to stop the server.
echo.
"%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port "%PORT%"
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:pip_failed
echo [ERROR] Could not install the required Python packages.
echo Run this manually for details: "%PYTHON%" -m pip install -r requirements.txt
exit /b 1

:help
echo NebrasCRM Windows launcher
 echo.
echo Usage: run.bat [port]
echo.
echo Environment variables:
echo   PORT=8008                 Server port ^(default: 8008^)
echo   PYTHON_BIN=C:\Path\python3.exe
 echo   CRM_DB_ENGINE=sqlite      Default local database
 echo   CRM_DB_ENGINE=mariadb     Use the configured MariaDB server
 echo   CRM_DB_ENGINE=mysql       Use the configured MySQL server
 echo   CRM_DB_ENGINE=postgresql  Use the configured PostgreSQL server
 echo   SEED_DEMO=1               Seed demo data in server database mode
exit /b 0
