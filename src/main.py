"""
Entry point da aplicação Wsi Break Time.
"""

import sys
import os

# Adiciona o diretório src ao path para imports funcionarem no .exe
if getattr(sys, 'frozen', False):
    # Executando como .exe
    sys.path.insert(0, sys._MEIPASS)
else:
    # Executando como script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    """Função principal."""
    # Habilita DPI awareness para telas de alta resolução
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Mantém rodando no tray
    app.setApplicationName("Wsi Break Time")
    app.setApplicationVersion("1.0.0")

    # Import absoluto para funcionar tanto em dev quanto no .exe
    from app import WsiBreakTimeApp

    wsi_break = WsiBreakTimeApp()
    wsi_break.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
