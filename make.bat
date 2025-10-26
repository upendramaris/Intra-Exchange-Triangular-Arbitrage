@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
  echo Usage: make ^<target^>
  echo Available targets: install format lint test run api migrate
  exit /b 1
)

set "TARGET=%~1"
shift

if defined POETRY (
  set "POETRY_CMD=%POETRY%"
) else (
  set "POETRY_CMD=python -m poetry"
)

if /I "%TARGET%"=="install" (
  call %POETRY_CMD% install %*
  exit /b !errorlevel!
)

if /I "%TARGET%"=="format" (
  call %POETRY_CMD% run ruff check --select I --fix . %*
  if errorlevel 1 exit /b !errorlevel!
  call %POETRY_CMD% run black . %*
  exit /b !errorlevel!
)

if /I "%TARGET%"=="lint" (
  call %POETRY_CMD% run ruff check . %*
  if errorlevel 1 exit /b !errorlevel!
  call %POETRY_CMD% run mypy triarb %*
  exit /b !errorlevel!
)

if /I "%TARGET%"=="test" (
  call %POETRY_CMD% run pytest %*
  exit /b !errorlevel!
)

if /I "%TARGET%"=="run" (
  call %POETRY_CMD% run python -m triarb.main %*
  exit /b !errorlevel!
)

if /I "%TARGET%"=="api" (
  set "ADMIN_PORT_VALUE=%ADMIN_PORT%"
  if "%ADMIN_PORT_VALUE%"=="" set "ADMIN_PORT_VALUE=8081"
  call %POETRY_CMD% run uvicorn triarb.api.server:app --host 0.0.0.0 --port %ADMIN_PORT_VALUE% %*
  exit /b !errorlevel!
)

if /I "%TARGET%"=="migrate" (
  call %POETRY_CMD% run alembic upgrade head %*
  exit /b !errorlevel!
)

echo Unknown target "%TARGET%"
exit /b 1
