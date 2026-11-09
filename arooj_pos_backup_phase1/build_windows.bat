@echo off
REM ========================================================
REM Arooj Cloth and Bedsheet Parda - Windows Desktop POS Build Script
REM Builds standalone executable via PyInstaller and creates Arooj_POS_Setup.exe via Inno Setup
REM ========================================================

echo [1/5] Checking Python environment...
python --version
if errorlevel 1 (
    echo Python is not found in PATH! Please install Python 3.10 or 3.11 from python.org.
    pause
    exit /b 1
)

echo [2/5] Creating and activating virtual environment...
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [3/5] Installing pinned dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/5] Running automated tests...
python tests\run_tests.py
if errorlevel 1 (
    echo Tests failed! Please review test output before packaging.
    pause
    exit /b 1
)

echo [5/5] Building standalone Windows executable with PyInstaller...
pyinstaller --noconfirm --clean arooj_pos.spec

echo.
echo ========================================================
echo PyInstaller build completed in dist\Arooj_POS\
echo.
echo If Inno Setup 6 is installed, compiling installer...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\Arooj_POS_Setup.iss
    echo Setup installer generated: dist\Arooj_POS_Setup.exe
) else (
    echo [Notice] Inno Setup 6 not found in standard directory.
    echo To generate the final single-file setup installer:
    echo 1. Download Inno Setup from: https://jrsoftware.org/isdl.php
    echo 2. Open installer\Arooj_POS_Setup.iss and click 'Compile'.
)
echo ========================================================
pause
