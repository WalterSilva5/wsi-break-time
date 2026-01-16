"""
Módulo de gerenciamento do ícone na bandeja do sistema (System Tray).
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import pyqtSignal, QObject
from pathlib import Path


class TrayIcon(QObject):
    """Gerenciador do ícone na bandeja do sistema."""

    # Sinais
    show_settings_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    skip_requested = pyqtSignal()
    take_break_now_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tray_icon = QSystemTrayIcon(parent)
        self._setup_icon()
        self._setup_menu()

        # Estado
        self.is_paused = False
        self.is_on_break = False

    def _setup_icon(self):
        """Configura o ícone do tray."""
        # Tenta carregar ícone personalizado ou cria um padrão
        icon_path = Path(__file__).parent.parent / 'resources' / 'icons' / 'app_icon.ico'

        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Cria um ícone simples programaticamente
            icon = self._create_default_icon()

        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Wsi Break Time - Proteção para seus olhos")

    def _create_default_icon(self, color: str = "#4CAF50") -> QIcon:
        """Cria um ícone padrão (olho estilizado)."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor("transparent"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Círculo de fundo
        painter.setBrush(QColor(color))
        painter.setPen(QColor(color))
        painter.drawEllipse(4, 4, size - 8, size - 8)

        # Letra "W" centralizada (de "Wsi")
        painter.setPen(QColor("white"))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x0084, "W")  # AlignCenter

        painter.end()

        return QIcon(pixmap)

    def _setup_menu(self):
        """Configura o menu de contexto."""
        self.menu = QMenu()

        # Status (não clicável)
        self.status_action = QAction("Próxima pausa em: --:--", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.menu.addSeparator()

        # Pausar/Retomar
        self.pause_action = QAction("Pausar", self.menu)
        self.pause_action.triggered.connect(self._on_pause_toggle)
        self.menu.addAction(self.pause_action)

        # Fazer pausa agora
        self.take_break_action = QAction("Fazer pausa agora", self.menu)
        self.take_break_action.triggered.connect(self.take_break_now_requested.emit)
        self.menu.addAction(self.take_break_action)

        # Pular pausa (só aparece durante a pausa)
        self.skip_action = QAction("Pular pausa", self.menu)
        self.skip_action.triggered.connect(self.skip_requested.emit)
        self.skip_action.setVisible(False)
        self.menu.addAction(self.skip_action)

        self.menu.addSeparator()

        # Configurações
        settings_action = QAction("Configurações...", self.menu)
        settings_action.triggered.connect(self.show_settings_requested.emit)
        self.menu.addAction(settings_action)

        self.menu.addSeparator()

        # Sair
        quit_action = QAction("Sair", self.menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)

        self.tray_icon.setContextMenu(self.menu)

        # Duplo clique abre configurações
        self.tray_icon.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Trata cliques no ícone."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_settings_requested.emit()

    def _on_pause_toggle(self):
        """Alterna entre pausar e retomar."""
        if self.is_paused:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()

    def show(self):
        """Mostra o ícone no tray."""
        self.tray_icon.show()

    def hide(self):
        """Esconde o ícone do tray."""
        self.tray_icon.hide()

    def show_notification(self, title: str, message: str,
                          icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                          duration_ms: int = 5000):
        """Exibe uma notificação do sistema."""
        self.tray_icon.showMessage(title, message, icon, duration_ms)

    def update_status(self, time_remaining: str):
        """Atualiza o texto de status no menu."""
        self.status_action.setText(f"Próxima pausa em: {time_remaining}")

    def set_paused_state(self, paused: bool):
        """Atualiza o estado de pausa."""
        self.is_paused = paused
        self.pause_action.setText("Retomar" if paused else "Pausar")

        if paused:
            self.status_action.setText("Timer pausado")
            # Muda ícone para indicar pausa
            self.tray_icon.setIcon(self._create_default_icon("#FFC107"))  # Amarelo
            self.tray_icon.setToolTip("Wsi Break Time - Pausado")
        else:
            self.tray_icon.setIcon(self._create_default_icon("#4CAF50"))  # Verde
            self.tray_icon.setToolTip("Wsi Break Time - Ativo")

    def set_break_state(self, on_break: bool):
        """Atualiza o estado durante uma pausa."""
        self.is_on_break = on_break
        self.skip_action.setVisible(on_break)
        self.take_break_action.setVisible(not on_break)
        self.pause_action.setVisible(not on_break)

        if on_break:
            self.status_action.setText("Em pausa...")
            self.tray_icon.setIcon(self._create_default_icon("#2196F3"))  # Azul
            self.tray_icon.setToolTip("Wsi Break Time - Descanse seus olhos")
