@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Wsi Break Time - Build Script
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    exit /b 1
)

echo [1/5] Checking dependencies...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo Installing PyQt6...
    pip install PyQt6
)

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo [2/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist src\__pycache__ rmdir /s /q src\__pycache__

echo [3/5] Running tests...
python run.py --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Application test failed, but continuing build...
)

echo [4/5] Building executable...
python -m PyInstaller build.spec --noconfirm

if not exist dist\WsiBreakTime.exe (
    echo ERROR: Build failed - executable not found
    exit /b 1
)

echo [5/5] Verifying build...
for %%A in (dist\WsiBreakTime.exe) do set size=%%~zA
set /a sizeMB=!size! / 1048576

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo Executable: dist\WsiBreakTime.exe
echo Size: !sizeMB! MB
echo.

REM Ask if user wants to run the executable
choice /C YN /M "Do you want to test the executable now"
if errorlevel 2 goto :end
if errorlevel 1 (
    echo.
    echo Running WsiBreakTime.exe...
    start "" "dist\WsiBreakTime.exe"
)

:end
echo.
echo Done!
pause
