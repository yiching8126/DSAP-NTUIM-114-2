@echo off
title LedgerLogic Setup
echo ========================================
echo   LedgerLogic 2.0 - Setup
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install dependencies
echo Installing rich...
python -m pip install rich
echo.

echo Installing pytest...
python -m pip install pytest
echo.

echo Installing pyinstaller (optional)...
python -m pip install pyinstaller
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo You can now run:
echo   python ledger.py
echo   pytest -v
echo.
pause