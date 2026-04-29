"""
Janela de confirmação de sessão.
Exibe uma janela comum (não fechável) com captcha que o usuário deve digitar
para confirmar a sessão. Não bloqueia a tela.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class BreakOverlay(QWidget):
    """Janela de confirmação de sessão (não fechável, não fullscreen)."""

    confirmed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.break_message = "Hora de descansar os olhos!\nOlhe para algo a 6 metros de distância."
        self.challenge_text = "mantenha o foco"
        self.fixed_message = ""
        self._allow_close = False

        self._setup_ui()
        self._setup_window()

    def force_close(self):
        """Permite fechar a janela (uso interno: encerramento da app)."""
        self._allow_close = True
        self.close()

    def _setup_window(self):
        """Configura propriedades da janela."""
        # Janela comum, sem botão de fechar e sem maximizar
        self.setWindowFlags(
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setWindowTitle("Confirmar sessão")
        self.resize(460, 420)

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        title_label = QLabel("Confirmar sessão")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Light))
        layout.addWidget(title_label)

        # Texto fixo (configurável)
        self.fixed_label = QLabel("")
        self.fixed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fixed_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.fixed_label.setWordWrap(True)
        self.fixed_label.setStyleSheet("""
            color: #1565C0;
            background-color: rgba(21, 101, 192, 20);
            border-left: 3px solid #1565C0;
            padding: 8px 12px;
            margin: 8px 0;
        """)
        self.fixed_label.hide()
        layout.addWidget(self.fixed_label)

        # Mensagem
        self.message_label = QLabel(self.break_message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setFont(QFont("Segoe UI", 12))
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #555555; margin: 15px 0;")
        layout.addWidget(self.message_label)

        layout.addSpacing(10)

        # Dica
        challenge_tip = QLabel("Digite o texto abaixo para confirmar:")
        challenge_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        challenge_tip.setFont(QFont("Segoe UI", 10))
        challenge_tip.setStyleSheet("color: #707070;")
        layout.addWidget(challenge_tip)

        # Texto do desafio
        self.challenge_label = QLabel(self.challenge_text)
        self.challenge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.challenge_label.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self.challenge_label.setStyleSheet("""
            color: #FF9800;
            background-color: rgba(255, 152, 0, 25);
            border: 1px solid #FF9800;
            border-radius: 8px;
            padding: 8px 18px;
            letter-spacing: 2px;
        """)
        layout.addWidget(self.challenge_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Input
        self.challenge_input = QLineEdit()
        self.challenge_input.setPlaceholderText("Digite aqui...")
        self.challenge_input.setFont(QFont("Consolas", 14))
        self.challenge_input.setMaximumWidth(380)
        self.challenge_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.challenge_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #BDBDBD;
                border-radius: 8px;
                padding: 8px 15px;
            }
            QLineEdit:focus {
                border-color: #FF9800;
            }
        """)
        self.challenge_input.textChanged.connect(self._on_challenge_text_changed)
        layout.addWidget(self.challenge_input, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_challenge_text_changed(self, text: str):
        """Confirma a sessão quando o texto digitado bate com o desafio."""
        if text.strip().lower() == self.challenge_text.strip().lower():
            self.confirmed.emit()

    def configure(self, message: str, challenge_text: str = "mantenha o foco",
                  fixed_message: str = ""):
        """Configura a janela antes de exibir."""
        self.break_message = message
        self.challenge_text = challenge_text
        self.fixed_message = fixed_message

        self.message_label.setText(message)
        self.challenge_label.setText(challenge_text)
        self.challenge_input.clear()

        trimmed = (fixed_message or "").strip()
        if trimmed:
            self.fixed_label.setText(trimmed)
            self.fixed_label.show()
        else:
            self.fixed_label.clear()
            self.fixed_label.hide()

    def show_window(self):
        """Exibe a janela centralizada no monitor primário."""
        self.challenge_input.clear()

        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.x() + (geometry.width() - self.width()) // 2
            y = geometry.y() + (geometry.height() - self.height()) // 2
            self.move(x, y)

        self.show()
        self.activateWindow()
        self.raise_()
        self.challenge_input.setFocus()

    def closeEvent(self, event):
        """Impede que a janela seja fechada pelo usuário (Alt+F4 etc.)."""
        if self._allow_close:
            event.accept()
        else:
            event.ignore()


class ConfirmToast(QWidget):
    """Pop-up tipo notificação no canto inferior direito com botão Confirmar."""

    MARGIN = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(320, 90)

        container = QWidget(self)
        container.setObjectName("toastContainer")
        container.setGeometry(0, 0, self.width(), self.height())
        container.setStyleSheet("""
            #toastContainer {
                background-color: #2C2C2C;
                border: 1px solid #1565C0;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)

        self.label = QLabel("confirmar sessão")
        self.label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label, stretch=1)

        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1E88E5;
            }
        """)
        self.confirm_button.clicked.connect(self.hide)
        layout.addWidget(self.confirm_button)

    def show_toast(self):
        """Exibe o toast no canto inferior direito sem roubar foco."""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.x() + geometry.width() - self.width() - self.MARGIN
            y = geometry.y() + geometry.height() - self.height() - self.MARGIN
            self.move(x, y)

        self.show()
        self.raise_()
