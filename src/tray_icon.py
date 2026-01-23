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
    complete_todo_requested = pyqtSignal(str)  # Emite todo_id

    # Sinais do Pomodoro
    start_pomodoro_requested = pyqtSignal()
    confirm_pomodoro_cycle_requested = pyqtSignal()
    end_pomodoro_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tray_icon = QSystemTrayIcon(parent)
        self._setup_icon()
        self._setup_menu()

        # Estado
        self.is_paused = False
        self.is_on_break = False
        self.pomodoro_active = False
        self.pomodoro_waiting_confirmation = False

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

        # TODOs submenu
        self.todos_menu = self.menu.addMenu("TODOs Pendentes")
        self._update_todos_menu_empty()

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

        # Seção Pomodoro
        self.pomodoro_separator = self.menu.addSeparator()

        # Iniciar Pomodoro (visível quando inativo)
        self.start_pomodoro_action = QAction("Iniciar Pomodoro", self.menu)
        self.start_pomodoro_action.triggered.connect(self.start_pomodoro_requested.emit)
        self.menu.addAction(self.start_pomodoro_action)

        # Confirmar próximo ciclo (visível quando aguardando confirmação)
        self.confirm_pomodoro_action = QAction("Iniciar próximo ciclo", self.menu)
        self.confirm_pomodoro_action.triggered.connect(self.confirm_pomodoro_cycle_requested.emit)
        self.confirm_pomodoro_action.setVisible(False)
        self.menu.addAction(self.confirm_pomodoro_action)

        # Encerrar Pomodoro (visível quando ativo)
        self.end_pomodoro_action = QAction("Encerrar Pomodoro", self.menu)
        self.end_pomodoro_action.triggered.connect(self.end_pomodoro_requested.emit)
        self.end_pomodoro_action.setVisible(False)
        self.menu.addAction(self.end_pomodoro_action)

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

    def _update_todos_menu_empty(self):
        """Configura menu de TODOs vazio."""
        self.todos_menu.clear()
        no_todos_action = QAction("Nenhum TODO pendente", self.todos_menu)
        no_todos_action.setEnabled(False)
        self.todos_menu.addAction(no_todos_action)

    def update_todos_menu(self, pending_todos: list):
        """Atualiza o submenu de TODOs pendentes."""
        self.todos_menu.clear()

        if not pending_todos:
            self._update_todos_menu_empty()
            return

        for todo in pending_todos:
            time_str = f" [{todo.scheduled_time}]" if todo.scheduled_time else ""
            recurring_icon = "[R] " if todo.is_recurring else ""
            action = QAction(f"{recurring_icon}{todo.title}{time_str}", self.todos_menu)
            # Usar lambda com valor padrão para capturar o id corretamente
            action.triggered.connect(lambda checked, tid=todo.id: self.complete_todo_requested.emit(tid))
            self.todos_menu.addAction(action)

        self.todos_menu.addSeparator()

        manage_action = QAction("Gerenciar TODOs...", self.todos_menu)
        manage_action.triggered.connect(self.show_settings_requested.emit)
        self.todos_menu.addAction(manage_action)

    def set_pomodoro_state(self, active: bool, waiting_confirmation: bool = False,
                           status_text: str = None):
        """Atualiza o estado do Pomodoro no menu."""
        self.pomodoro_active = active
        self.pomodoro_waiting_confirmation = waiting_confirmation

        # Visibilidade dos itens
        self.start_pomodoro_action.setVisible(not active)
        self.end_pomodoro_action.setVisible(active)
        self.confirm_pomodoro_action.setVisible(active and waiting_confirmation)

        # Esconde itens de pausa regular quando Pomodoro está ativo
        self.pause_action.setVisible(not active and not self.is_on_break)
        self.take_break_action.setVisible(not active and not self.is_on_break)

        # Atualiza status e ícone
        if active:
            if status_text:
                self.status_action.setText(f"Pomodoro: {status_text}")
            if waiting_confirmation:
                self.tray_icon.setIcon(self._create_default_icon("#FF9800"))  # Laranja
                self.tray_icon.setToolTip("Pomodoro - Aguardando confirmação")
            else:
                self.tray_icon.setIcon(self._create_default_icon("#E91E63"))  # Rosa/Magenta
                self.tray_icon.setToolTip("Pomodoro - Ativo")
        else:
            self.tray_icon.setIcon(self._create_default_icon("#4CAF50"))  # Verde
            self.tray_icon.setToolTip("Wsi Break Time - Ativo")

    def update_pomodoro_status(self, status_text: str):
        """Atualiza apenas o texto de status do Pomodoro."""
        if self.pomodoro_active:
            self.status_action.setText(f"Pomodoro: {status_text}")
