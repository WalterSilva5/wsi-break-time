#!/usr/bin/env python3
"""
Build script for Wsi Break Time
Supports Windows, Linux, and macOS
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def run_command(cmd, check=True):
    """Execute a shell command."""
    try:
        result = subprocess.run(cmd, shell=True, check=check,
                              capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return False


def check_python():
    """Verify Python installation."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("ERROR: Python 3.9+ required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def install_dependencies():
    """Install required packages."""
    print("\n[1/5] Checking dependencies...")
    packages = ["PyQt6", "pyinstaller"]

    for package in packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✓ {package} installed")
        except ImportError:
            print(f"Installing {package}...")
            if not run_command(f"{sys.executable} -m pip install {package}"):
                print(f"ERROR: Failed to install {package}")
                sys.exit(1)


def clean_build():
    """Remove previous build artifacts."""
    print("\n[2/5] Cleaning previous builds...")
    dirs_to_remove = ["build", "dist", "__pycache__", "src/__pycache__"]

    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ Removed {dir_name}")


def run_tests():
    """Run basic tests."""
    print("\n[3/5] Running tests...")
    if run_command(f"{sys.executable} -c 'import src.main'", check=False):
        print("✓ Import test passed")
    else:
        print("⚠ Import test failed, but continuing...")


def build_executable():
    """Build the executable using PyInstaller."""
    print("\n[4/5] Building executable...")
    cmd = f"{sys.executable} -m PyInstaller build.spec --noconfirm"

    if not run_command(cmd):
        print("ERROR: Build failed")
        sys.exit(1)

    print("✓ Build completed")


def verify_build():
    """Verify the built executable."""
    print("\n[5/5] Verifying build...")

    exe_name = "WsiBreakTime.exe" if sys.platform == "win32" else "WsiBreakTime"
    exe_path = Path("dist") / exe_name

    if not exe_path.exists():
        print(f"ERROR: Executable not found at {exe_path}")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✓ Executable: {exe_path}")
    print(f"✓ Size: {size_mb:.1f} MB")

    return exe_path


def main():
    """Main build process."""
    print("=" * 50)
    print("Wsi Break Time - Build Script")
    print("=" * 50)

    check_python()
    install_dependencies()
    clean_build()
    run_tests()
    build_executable()
    exe_path = verify_build()

    print("\n" + "=" * 50)
    print("Build completed successfully!")
    print("=" * 50)
    print(f"\nExecutable ready: {exe_path}")

    if "--run" in sys.argv:
        print(f"\nRunning {exe_path}...")
        subprocess.Popen([str(exe_path)])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
