@echo off
cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

:: Check required packages
echo Checking dependencies...
python -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo [WARN] 'rich' not found. Running setup...
    call setup.bat
    goto :run
)

python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [WARN] 'pytest' not found. Running setup...
    call setup.bat
    goto :run
)

:run
echo Starting LedgerLogic...
python ledger.py
pause