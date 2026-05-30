@echo off
title LedgerLogic Test Suite Demo
echo ========================================
echo Running LedgerLogic 2.0 Test Suite
echo ========================================
echo.

pytest tests/test_budget.py -v
echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul
cls

pytest tests/test_cli.py -v
echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul
cls

pytest tests/test_ledger.py -v
echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul
cls

pytest tests/test_macros.py -v
echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul
cls

pytest tests/test_typo.py -v
echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul
cls

pytest tests/test_benchmark.py -v
echo.
echo ========================================
echo All tests completed.
echo ========================================
pause