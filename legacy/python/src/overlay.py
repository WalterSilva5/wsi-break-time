"""
Módulo de overlay fullscreen para pausas.
Exibe uma tela escura com mensagem durante as pausas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QScreen


class BreakOverlay(QWidget):
    """Overlay fullscreen para pausas."""

    skip_requested = pyqtSignal()
    postpone_requested = pyqtSignal(int)  # Emite minutos para adiar

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configurações
        self.allow_skip = True
        self.allow_postpone = True
        self.postpone_minutes = 5
        self.break_message = "Hora de descansar os olhos!\nOlhe para algo a 6 metros de distância."
        self.break_duration = 20

        self._setup_ui()
        self._setup_window()

    def _setup_window(self):
        """Configura propriedades da janela."""
        # Fullscreen sem bordas
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # Fundo semi-transparente escuro
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 230);
            }
        """)

        # Pega a tela principal
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        title_label = QLabel("Pausa para os olhos")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 36, QFont.Weight.Light))
        title_label.setStyleSheet("color: white; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # Mensagem principal
        self.message_label = QLabel(self.break_message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setFont(QFont("Segoe UI", 18))
        self.message_label.setStyleSheet("color: #B0B0B0; margin: 30px;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # Contador
        self.countdown_label = QLabel("20")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setFont(QFont("Segoe UI", 72, QFont.Weight.Bold))
        self.countdown_label.setStyleSheet("color: #4CAF50; margin: 20px;")
        layout.addWidget(self.countdown_label)

        # Texto do contador
        seconds_text = QLabel("segundos restantes")
        seconds_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seconds_text.setFont(QFont("Segoe UI", 14))
        seconds_text.setStyleSheet("color: #808080;")
        layout.addWidget(seconds_text)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(400)
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333333;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Espaçamento
        layout.addSpacing(40)

        # Botões
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)

        # Botão Pular
        self.skip_button = QPushButton("Pular")
        self.skip_button.setFont(QFont("Segoe UI", 12))
        self.skip_button.setMinimumSize(120, 40)
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #757575;
            }
        """)
        self.skip_button.clicked.connect(self.skip_requested.emit)
        button_layout.addWidget(self.skip_button)

        # Botão Adiar
        self.postpone_button = QPushButton(f"Adiar {self.postpone_minutes} min")
        self.postpone_button.setFont(QFont("Segoe UI", 12))
        self.postpone_button.setMinimumSize(140, 40)
        self.postpone_button.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1E88E5;
            }
        """)
        self.postpone_button.clicked.connect(
            lambda: self.postpone_requested.emit(self.postpone_minutes)
        )
        button_layout.addWidget(self.postpone_button)

        layout.addLayout(button_layout)

        # Dica
        tip_label = QLabel("Pressione ESC para pular")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setFont(QFont("Segoe UI", 10))
        tip_label.setStyleSheet("color: #505050; margin-top: 30px;")
        layout.addWidget(tip_label)

    def configure(self, message: str, duration: int, allow_skip: bool,
                  allow_postpone: bool, postpone_minutes: int):
        """Configura o overlay antes de exibir."""
        self.break_message = message
        self.break_duration = duration
        self.allow_skip = allow_skip
        self.allow_postpone = allow_postpone
        self.postpone_minutes = postpone_minutes

        self.message_label.setText(message)
        self.progress_bar.setMaximum(duration)
        self.progress_bar.setValue(duration)

        self.skip_button.setVisible(allow_skip)
        self.postpone_button.setVisible(allow_postpone)
        self.postpone_button.setText(f"Adiar {postpone_minutes} min")

    def update_countdown(self, seconds_remaining: int):
        """Atualiza o contador e a barra de progresso."""
        self.countdown_label.setText(str(seconds_remaining))
        self.progress_bar.setValue(seconds_remaining)

        # Muda cor quando está acabando
        if seconds_remaining <= 5:
            self.countdown_label.setStyleSheet("color: #FF9800; margin: 20px;")
        else:
            self.countdown_label.setStyleSheet("color: #4CAF50; margin: 20px;")

    def show_fullscreen(self):
        """Exibe o overlay em todas as telas."""
        # Pega a tela principal e mostra fullscreen nela
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)

        self.countdown_label.setText(str(self.break_duration))
        self.progress_bar.setValue(self.break_duration)
        self.countdown_label.setStyleSheet("color: #4CAF50; margin: 20px;")

        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    def keyPressEvent(self, event):
        """Trata teclas pressionadas."""
        if event.key() == Qt.Key.Key_Escape and self.allow_skip:
            self.skip_requested.emit()
        else:
            super().keyPressEvent(event)


class MultiScreenOverlay:
    """Gerencia overlays em múltiplas telas."""

    def __init__(self):
        self.overlays: list[BreakOverlay] = []

    def create_overlays(self) -> BreakOverlay:
        """Cria overlays para todas as telas e retorna o principal."""
        self.close_all()
        self.overlays = []

        screens = QApplication.screens()
        main_overlay = None

        for i, screen in enumerate(screens):
            overlay = BreakOverlay()
            geometry = screen.geometry()
            overlay.setGeometry(geometry)

            if i == 0:
                main_overlay = overlay
            else:
                # Overlays secundários não têm botões
                overlay.skip_button.hide()
                overlay.postpone_button.hide()

            self.overlays.append(overlay)

        return main_overlay

    def show_all(self):
        """Exibe todos os overlays."""
        for overlay in self.overlays:
            overlay.showFullScreen()
            overlay.activateWindow()

    def update_all(self, seconds_remaining: int):
        """Atualiza contador em todos os overlays."""
        for overlay in self.overlays:
            overlay.update_countdown(seconds_remaining)

    def close_all(self):
        """Fecha todos os overlays."""
        for overlay in self.overlays:
            overlay.close()
        self.overlays = []

    def configure_all(self, message: str, duration: int, allow_skip: bool,
                      allow_postpone: bool, postpone_minutes: int):
        """Configura todos os overlays."""
        for overlay in self.overlays:
            overlay.configure(message, duration, allow_skip, allow_postpone, postpone_minutes)
