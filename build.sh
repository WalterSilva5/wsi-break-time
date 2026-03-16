#!/bin/bash
set -e

case "${1:-debug}" in
    release)
        echo "Building release..."
        cargo build --release
        echo ""
        echo "Build completo: target/release/wsi-break-time"
        ;;
    clean)
        cargo clean
        echo "Limpo."
        ;;
    *)
        echo "Building debug..."
        cargo build
        echo ""
        echo "Build completo: target/debug/wsi-break-time"
        ;;
esac
