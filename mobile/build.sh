#!/bin/bash
# Build script para geração do APK - Wsi Break Time (Android)
#
# Uso:
#   ./build.sh          # Build APK debug
#   ./build.sh release  # Build APK release
#   ./build.sh clean    # Limpa build anterior
#
# Pré-requisitos:
#   - Flutter SDK instalado e no PATH
#   - Android SDK configurado
#   - Java JDK 17+

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Wsi Break Time - Build Android ===${NC}"
echo ""

# Verifica Flutter
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}Erro: Flutter não encontrado no PATH${NC}"
    echo "Instale o Flutter: https://flutter.dev/docs/get-started/install"
    exit 1
fi

echo -e "${YELLOW}Flutter version:${NC}"
flutter --version | head -1
echo ""

MODE="${1:-debug}"

case "$MODE" in
    clean)
        echo -e "${YELLOW}Limpando build anterior...${NC}"
        flutter clean
        echo -e "${GREEN}Build limpo com sucesso!${NC}"
        ;;

    release)
        echo -e "${YELLOW}Instalando dependências...${NC}"
        flutter pub get

        echo -e "${YELLOW}Analisando código...${NC}"
        flutter analyze --no-fatal-infos || true

        echo -e "${YELLOW}Gerando APK release...${NC}"
        flutter build apk --release

        APK_PATH="build/app/outputs/flutter-apk/app-release.apk"
        if [ -f "$APK_PATH" ]; then
            SIZE=$(du -h "$APK_PATH" | cut -f1)
            echo ""
            echo -e "${GREEN}=== Build concluído com sucesso! ===${NC}"
            echo -e "APK: ${YELLOW}$APK_PATH${NC}"
            echo -e "Tamanho: ${YELLOW}$SIZE${NC}"
        else
            echo -e "${RED}Erro: APK não foi gerado${NC}"
            exit 1
        fi
        ;;

    debug|*)
        echo -e "${YELLOW}Instalando dependências...${NC}"
        flutter pub get

        echo -e "${YELLOW}Gerando APK debug...${NC}"
        flutter build apk --debug

        APK_PATH="build/app/outputs/flutter-apk/app-debug.apk"
        if [ -f "$APK_PATH" ]; then
            SIZE=$(du -h "$APK_PATH" | cut -f1)
            echo ""
            echo -e "${GREEN}=== Build concluído com sucesso! ===${NC}"
            echo -e "APK: ${YELLOW}$APK_PATH${NC}"
            echo -e "Tamanho: ${YELLOW}$SIZE${NC}"
        else
            echo -e "${RED}Erro: APK não foi gerado${NC}"
            exit 1
        fi
        ;;
esac
