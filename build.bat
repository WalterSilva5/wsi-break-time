@echo off
setlocal

if "%1"=="release" (
    echo Building release...
    cargo build --release
    echo.
    echo Build completo: target\release\wsi-break-time.exe
) else if "%1"=="clean" (
    cargo clean
    echo Limpo.
) else (
    echo Building debug...
    cargo build
    echo.
    echo Build completo: target\debug\wsi-break-time.exe
)
