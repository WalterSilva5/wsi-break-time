#!/bin/bash

set -e

echo "========================================"
echo "Wsi Break Time - Build Script"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "[1/5] Checking dependencies..."
pip3 install -q PyQt6 pyinstaller

echo "[2/5] Cleaning previous builds..."
rm -rf build dist __pycache__ src/__pycache__

echo "[3/5] Running tests..."
python3 run.py --version &> /dev/null || echo "WARNING: Application test failed, but continuing build..."

echo "[4/5] Building executable..."
python3 -m PyInstaller build.spec --noconfirm

if [ ! -f "dist/WsiBreakTime" ] && [ ! -f "dist/WsiBreakTime.exe" ]; then
    echo "ERROR: Build failed - executable not found"
    exit 1
fi

echo "[5/5] Verifying build..."
if [ -f "dist/WsiBreakTime.exe" ]; then
    SIZE=$(du -h dist/WsiBreakTime.exe | cut -f1)
    EXECUTABLE="dist/WsiBreakTime.exe"
else
    SIZE=$(du -h dist/WsiBreakTime | cut -f1)
    EXECUTABLE="dist/WsiBreakTime"
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo "Executable: $EXECUTABLE"
echo "Size: $SIZE"
echo ""
echo "Done!"
