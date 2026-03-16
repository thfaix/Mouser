@echo off
:: ──────────────────────────────────────────────────────────────
:: setup.bat — Set up the Mouser development environment
::
:: This script:
::   1. Detects the Python executable (py / python / python3)
::   2. Creates a virtual environment in .venv
::   3. Activates it and installs all dependencies
::
:: Usage:  setup.bat
:: ──────────────────────────────────────────────────────────────
title Mouser — Setup
cd /d "%~dp0"
set "MAIN_SCRIPT=main_qml.py"

echo.
echo ===  Mouser — Environment Setup  ===
echo.

:: ── 1. Detect Python executable ──────────────────────────────
set "PYTHON_CMD="

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :found_python
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :found_python
)

echo [ERROR] Python not found.
echo         Please install Python 3.10+ from https://www.python.org/downloads/
echo         Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found_python
for /f "tokens=*" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do echo [*] Found: %%v
echo [*] Using command: %PYTHON_CMD%
echo.

:: ── 2. Create virtual environment ────────────────────────────
if exist ".venv\Scripts\activate.bat" (
    echo [*] Virtual environment already exists — skipping creation
) else (
    echo [*] Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [*] Virtual environment created in .venv
)
echo.

:: ── 3. Activate venv and install dependencies ─────────────────
echo [*] Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo [*] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ===  Setup complete!  ===
echo.
echo To run Mouser:
echo   .venv\Scripts\python.exe %MAIN_SCRIPT%
echo   — or —
echo   Mouser.bat
echo.
pause
