@echo off
REM Build script para geração do APK - Wsi Break Time (Android)
REM
REM Uso:
REM   build.bat          - Build APK debug
REM   build.bat release  - Build APK release
REM   build.bat clean    - Limpa build anterior
REM
REM Pré-requisitos:
REM   - Flutter SDK instalado e no PATH
REM   - Android SDK configurado
REM   - Java JDK 17+

cd /d "%~dp0"

echo === Wsi Break Time - Build Android ===
echo.

where flutter >nul 2>nul
if errorlevel 1 (
    echo Erro: Flutter nao encontrado no PATH
    echo Instale o Flutter: https://flutter.dev/docs/get-started/install
    exit /b 1
)

flutter --version | findstr /n "." | findstr "^1:"
echo.

set MODE=%1
if "%MODE%"=="" set MODE=debug

if "%MODE%"=="clean" (
    echo Limpando build anterior...
    flutter clean
    echo Build limpo com sucesso!
    goto :end
)

if "%MODE%"=="release" (
    echo Instalando dependencias...
    flutter pub get

    echo Analisando codigo...
    flutter analyze --no-fatal-infos

    echo Gerando APK release...
    flutter build apk --release

    set APK_PATH=build\app\outputs\flutter-apk\app-release.apk
    if exist "%APK_PATH%" (
        echo.
        echo === Build concluido com sucesso! ===
        echo APK: %APK_PATH%
    ) else (
        echo Erro: APK nao foi gerado
        exit /b 1
    )
    goto :end
)

REM Default: debug
echo Instalando dependencias...
flutter pub get

echo Gerando APK debug...
flutter build apk --debug

set APK_PATH=build\app\outputs\flutter-apk\app-debug.apk
if exist "%APK_PATH%" (
    echo.
    echo === Build concluido com sucesso! ===
    echo APK: %APK_PATH%
) else (
    echo Erro: APK nao foi gerado
    exit /b 1
)

:end
