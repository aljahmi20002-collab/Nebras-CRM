@echo off
rem Build and start the complete NebrasCRM + MySQL 8.4 Docker Compose stack.
rem Usage: compose-up.bat [--reset-data]
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "RESET_DATA="
if /I "%~1"=="--reset-data" (
  set "RESET_DATA=1"
  shift
)

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker Desktop is required.
  exit /b 1
)

docker compose version >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker Compose is not available. Start Docker Desktop and try again.
  exit /b 1
)

if not exist ".env.docker" (
  where python3 >nul 2>nul
  if errorlevel 1 goto :copy_template
  python3 create_docker_env.py .env.docker
  if errorlevel 1 goto :copy_template
  echo [INFO] Created a private .env.docker with random passwords and CRM secrets.
  goto :validate_env
)

goto :validate_env

:copy_template
copy /y .env.docker.example .env.docker >nul
echo [INFO] Created .env.docker from the example because python3 was not available.
echo [INFO] Replace every placeholder password and CRM secret, then run compose-up.bat again.
exit /b 1

:validate_env
rem Compose interpolates ${...} before applying env_file, so diagnose missing
rem values here rather than letting it fail with an opaque interpolation error.
set "ENV_ERROR="
for %%V in (CRM_SECRET CRM_PORTAL_SECRET CRM_AGENT_PORTAL_SECRET CRM_WEBHOOK_SECRET MYSQL_DATABASE MYSQL_USER MYSQL_PASSWORD MYSQL_ROOT_PASSWORD) do (
  findstr /R /C:"^%%V=." .env.docker >nul
  if errorlevel 1 (
    echo [ERROR] Required value %%V is missing or blank in .env.docker.
    set "ENV_ERROR=1"
  )
)
if defined RESET_DATA (
  for %%V in (CRM_BOOTSTRAP_ADMIN_EMAIL CRM_BOOTSTRAP_ADMIN_NAME CRM_BOOTSTRAP_ADMIN_PASSWORD) do (
    findstr /R /C:"^%%V=." .env.docker >nul
    if errorlevel 1 (
      echo [ERROR] Required value %%V is missing or blank for a fresh database.
      set "ENV_ERROR=1"
    )
  )
)
if defined ENV_ERROR (
  echo [INFO] Do not run Docker Compose without --env-file .env.docker.
  echo [INFO] For a disposable test configuration: del .env.docker ^&^& compose-up.bat --reset-data
  exit /b 1
)

findstr /I /C:"=replace-with-" .env.docker >nul
if not errorlevel 1 (
  echo [ERROR] Replace the placeholder passwords and CRM secrets in .env.docker first.
  exit /b 1
)

if defined RESET_DATA (
  echo [INFO] Deleting the disposable local MySQL database volume...
  docker compose --env-file .env.docker -f docker-compose.yml down -v --remove-orphans
  if errorlevel 1 echo [WARN] The previous stack could not be stopped cleanly; continuing with a fresh start.
)

docker compose --env-file .env.docker -f docker-compose.yml up -d --build --remove-orphans
if errorlevel 1 (
  echo.
  echo [ERROR] Docker Compose could not start. Recent MySQL logs:
  docker compose --env-file .env.docker -f docker-compose.yml logs --tail=120 mysql
  echo.
  echo [INFO] If this is only test data, reset the local Docker database with:
  echo compose-up.bat --reset-data
  exit /b 1
)

set "APP_PORT=8008"
for /f "tokens=1,* delims==" %%A in ('findstr /B /C:"NEBRAS_PORT=" .env.docker') do set "APP_PORT=%%B"
set "BOOTSTRAP_EMAIL=admin@nebrascrm.local"
for /f "tokens=1,* delims==" %%A in ('findstr /B /C:"CRM_BOOTSTRAP_ADMIN_EMAIL=" .env.docker') do set "BOOTSTRAP_EMAIL=%%B"
echo.
echo [OK] NebrasCRM is running with MySQL 8.4 at http://localhost:%APP_PORT%/app
echo [INFO] First login on a new database: %BOOTSTRAP_EMAIL%
echo [INFO] The first-login password is stored privately in CRM_BOOTSTRAP_ADMIN_PASSWORD in .env.docker.
echo [INFO] View status: docker compose --env-file .env.docker -f docker-compose.yml ps
endlocal
exit /b 0
