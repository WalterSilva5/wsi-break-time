"""
Classe principal da aplicação Wsi Break Time.
Integra todos os componentes: timer, tray, overlay e configurações.
"""

import random
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QCheckBox, QTextEdit, QPushButton, QGroupBox,
    QFormLayout, QTabWidget, QWidget, QSystemTrayIcon,
    QListWidget, QListWidgetItem, QMessageBox, QTimeEdit, QLineEdit
)
from PyQt6.QtCore import QTimer, Qt, QTime
from PyQt6.QtGui import QFont

from settings import SettingsManager, AppSettings
from timer_manager import TimerManager
from tray_icon import TrayIcon
from overlay import BreakOverlay, MultiScreenOverlay
from todo_model import TodoItem, TodoStatus
from todo_manager import TodoManager


class TodoVerificationDialog(QDialog):
    """Diálogo para verificação de código ao completar TODO recorrente."""

    def __init__(self, todo: TodoItem, verification_code: str, parent=None):
        super().__init__(parent)
        self.todo = todo
        self.verification_code = verification_code
        self.setWindowTitle("Completar TODO")
        self.setMinimumSize(400, 280)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(f"Completar: {self.todo.title}")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description (if any)
        if self.todo.description:
            desc_label = QLabel(self.todo.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray;")
            layout.addWidget(desc_label)

        layout.addSpacing(20)

        # Verification code display
        code_group = QGroupBox("Digite o código abaixo para confirmar")
        code_layout = QVBoxLayout()

        code_display = QLabel(self.verification_code)
        code_display.setFont(QFont("Consolas", 24, QFont.Weight.Bold))
        code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_display.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 15px;
                letter-spacing: 5px;
            }
        """)
        code_layout.addWidget(code_display)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Digite o código aqui...")
        self.code_input.setFont(QFont("Consolas", 16))
        self.code_input.setMaxLength(8)
        self.code_input.textChanged.connect(self._on_text_changed)
        code_layout.addWidget(self.code_input)

        code_group.setLayout(code_layout)
        layout.addWidget(code_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.confirm_btn = QPushButton("Confirmar")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)

    def _on_text_changed(self, text: str):
        """Habilita botão quando código está completo."""
        self.confirm_btn.setEnabled(len(text) == 8)

    def _on_confirm(self):
        """Verifica código e aceita se correto."""
        if self.code_input.text().upper() == self.verification_code.upper():
            self.accept()
        else:
            QMessageBox.warning(self, "Código Incorreto",
                              "O código digitado não confere. Tente novamente.")
            self.code_input.clear()
            self.code_input.setFocus()

    def get_entered_code(self) -> str:
        """Retorna o código digitado."""
        return self.code_input.text()


class SettingsDialog(QDialog):
    """Diálogo de configurações."""

    def __init__(self, settings: AppSettings, timer_manager: Optional[TimerManager] = None,
                 todos: Optional[List[TodoItem]] = None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.timer_manager = timer_manager
        self._todos = todos if todos else []
        self._editing_todo_id = None  # ID do TODO sendo editado
        self.setWindowTitle("Configurações - Wsi Break Time")
        self.setMinimumSize(500, 600)
        self._setup_ui()
        self._load_settings()

        # Timer para atualizar informações da próxima pausa
        if self.timer_manager:
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self._update_next_break_info)
            self.update_timer.start(1000)  # Atualiza a cada segundo
            self._update_next_break_info()  # Atualização inicial

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)

        # Tabs
        tabs = QTabWidget()

        # Tab: Pausas
        breaks_tab = QWidget()
        breaks_layout = QVBoxLayout(breaks_tab)

        # Grupo: Intervalo
        interval_group = QGroupBox("Intervalo")
        interval_layout = QFormLayout()

        self.break_interval_spin = QSpinBox()
        self.break_interval_spin.setRange(1, 120)
        self.break_interval_spin.setSuffix(" minutos")
        interval_layout.addRow("Pausa a cada:", self.break_interval_spin)

        self.break_duration_spin = QSpinBox()
        self.break_duration_spin.setRange(5, 300)
        self.break_duration_spin.setSuffix(" segundos")
        interval_layout.addRow("Duração da pausa:", self.break_duration_spin)

        interval_group.setLayout(interval_layout)
        breaks_layout.addWidget(interval_group)

        # Grupo: Próxima Pausa (somente se timer estiver disponível)
        if self.timer_manager:
            status_group = QGroupBox("Próxima Pausa")
            status_layout = QFormLayout()

            self.next_break_time_label = QLabel("--:--")
            self.next_break_time_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            status_layout.addRow("Horário:", self.next_break_time_label)

            self.time_remaining_label = QLabel("--:--")
            self.time_remaining_label.setFont(QFont("Arial", 12))
            status_layout.addRow("Tempo restante:", self.time_remaining_label)

            status_group.setLayout(status_layout)
            breaks_layout.addWidget(status_group)

        # Grupo: Notificações
        notify_group = QGroupBox("Notificações")
        notify_layout = QFormLayout()

        self.pre_notify_check = QCheckBox("Notificar antes da pausa")
        notify_layout.addRow(self.pre_notify_check)

        self.pre_notify_spin = QSpinBox()
        self.pre_notify_spin.setRange(5, 120)
        self.pre_notify_spin.setSuffix(" segundos antes")
        notify_layout.addRow("Antecedência:", self.pre_notify_spin)

        self.play_sound_check = QCheckBox("Tocar som de alerta")
        notify_layout.addRow(self.play_sound_check)

        notify_group.setLayout(notify_layout)
        breaks_layout.addWidget(notify_group)

        # Grupo: Controles
        controls_group = QGroupBox("Controles")
        controls_layout = QFormLayout()

        self.allow_skip_check = QCheckBox("Permitir pular pausas")
        controls_layout.addRow(self.allow_skip_check)

        self.allow_postpone_check = QCheckBox("Permitir adiar pausas")
        controls_layout.addRow(self.allow_postpone_check)

        self.postpone_spin = QSpinBox()
        self.postpone_spin.setRange(1, 30)
        self.postpone_spin.setSuffix(" minutos")
        controls_layout.addRow("Tempo de adiamento:", self.postpone_spin)

        controls_group.setLayout(controls_layout)
        breaks_layout.addWidget(controls_group)

        breaks_layout.addStretch()
        tabs.addTab(breaks_tab, "Pausas")

        # Tab: Mensagens
        messages_tab = QWidget()
        messages_layout = QVBoxLayout(messages_tab)

        messages_label = QLabel("Mensagens exibidas durante a pausa (seleção aleatória):")
        messages_layout.addWidget(messages_label)

        # Lista de mensagens
        self.messages_list = QListWidget()
        self.messages_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.messages_list.itemDoubleClicked.connect(self._edit_message)
        messages_layout.addWidget(self.messages_list)

        # Campo para adicionar/editar mensagem
        self.message_edit = QTextEdit()
        self.message_edit.setMaximumHeight(80)
        self.message_edit.setPlaceholderText("Digite uma nova mensagem aqui...")
        messages_layout.addWidget(self.message_edit)

        # Botões de gerenciamento
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Adicionar")
        add_btn.clicked.connect(self._add_message)
        btn_layout.addWidget(add_btn)

        update_btn = QPushButton("Atualizar Selecionada")
        update_btn.clicked.connect(self._update_message)
        btn_layout.addWidget(update_btn)

        remove_btn = QPushButton("Remover")
        remove_btn.clicked.connect(self._remove_message)
        btn_layout.addWidget(remove_btn)

        messages_layout.addLayout(btn_layout)

        tip_label = QLabel("Dica: Duplo clique em uma mensagem para editá-la")
        tip_label.setStyleSheet("color: gray; font-size: 11px;")
        messages_layout.addWidget(tip_label)

        tabs.addTab(messages_tab, "Mensagens")

        # Tab: Geral
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # Grupo: Inicialização
        startup_group = QGroupBox("Inicialização")
        startup_layout = QVBoxLayout()

        self.start_minimized_check = QCheckBox("Iniciar minimizado")
        startup_layout.addWidget(self.start_minimized_check)

        self.start_windows_check = QCheckBox("Iniciar com o Windows")
        startup_layout.addWidget(self.start_windows_check)

        startup_group.setLayout(startup_layout)
        general_layout.addWidget(startup_group)

        # Grupo: Extras
        extras_group = QGroupBox("Extras")
        extras_layout = QFormLayout()

        self.water_reminder_spin = QSpinBox()
        self.water_reminder_spin.setRange(0, 120)
        self.water_reminder_spin.setSuffix(" minutos")
        self.water_reminder_spin.setSpecialValueText("Desativado")
        extras_layout.addRow("Lembrete de água:", self.water_reminder_spin)

        extras_group.setLayout(extras_layout)
        general_layout.addWidget(extras_group)

        general_layout.addStretch()
        tabs.addTab(general_tab, "Geral")

        # Tab: TODOs
        todos_tab = self._setup_todos_tab()
        tabs.addTab(todos_tab, "TODOs")

        layout.addWidget(tabs)

        # Botões principais
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Carrega as configurações atuais."""
        self.break_interval_spin.setValue(self.settings.break_interval)
        self.break_duration_spin.setValue(self.settings.break_duration)
        self.pre_notify_check.setChecked(self.settings.show_pre_notification)
        self.pre_notify_spin.setValue(self.settings.pre_notification_seconds)
        self.play_sound_check.setChecked(self.settings.play_sound)
        self.allow_skip_check.setChecked(self.settings.allow_skip)
        self.allow_postpone_check.setChecked(self.settings.allow_postpone)
        self.postpone_spin.setValue(self.settings.postpone_minutes)
        self.start_minimized_check.setChecked(self.settings.start_minimized)
        self.start_windows_check.setChecked(self.settings.start_with_windows)
        self.water_reminder_spin.setValue(self.settings.water_reminder_interval)

        # Carrega lista de mensagens
        self.messages_list.clear()
        for msg in self.settings.break_messages:
            self.messages_list.addItem(msg)

    def _add_message(self):
        """Adiciona uma nova mensagem à lista."""
        text = self.message_edit.toPlainText().strip()
        if text:
            self.messages_list.addItem(text)
            self.message_edit.clear()

    def _update_message(self):
        """Atualiza a mensagem selecionada."""
        current_item = self.messages_list.currentItem()
        if current_item:
            text = self.message_edit.toPlainText().strip()
            if text:
                current_item.setText(text)
                self.message_edit.clear()

    def _remove_message(self):
        """Remove a mensagem selecionada."""
        current_row = self.messages_list.currentRow()
        if current_row >= 0:
            if self.messages_list.count() > 1:
                self.messages_list.takeItem(current_row)
            else:
                QMessageBox.warning(
                    self, "Aviso",
                    "Deve haver pelo menos uma mensagem na lista."
                )

    def _edit_message(self, item: QListWidgetItem):
        """Carrega a mensagem selecionada no campo de edição."""
        self.message_edit.setPlainText(item.text())

    def _update_next_break_info(self):
        """Atualiza as informações da próxima pausa."""
        # Verifica se os labels existem (só existem se timer_manager foi passado)
        if not hasattr(self, 'next_break_time_label'):
            return

        if not self.timer_manager or not self.timer_manager.is_running:
            self.next_break_time_label.setText("Timer pausado")
            self.time_remaining_label.setText("--:--")
            return

        if self.timer_manager.is_on_break:
            self.next_break_time_label.setText("Em pausa agora")
            self.time_remaining_label.setText("--:--")
            return

        # Obtém o tempo restante
        remaining = self.timer_manager.get_time_until_break()
        total_seconds = int(remaining.total_seconds())

        if total_seconds > 0:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            self.time_remaining_label.setText(f"{minutes:02d}:{seconds:02d}")
        else:
            self.time_remaining_label.setText("00:00")

        # Obtém o horário da próxima pausa
        if self.timer_manager.next_break_time:
            next_time = self.timer_manager.next_break_time.strftime("%H:%M:%S")
            self.next_break_time_label.setText(next_time)
        else:
            self.next_break_time_label.setText("--:--")

    def closeEvent(self, event):
        """Chamado quando o diálogo é fechado."""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        super().closeEvent(event)

    def _setup_todos_tab(self) -> QWidget:
        """Configura a aba de TODOs."""
        todos_tab = QWidget()
        layout = QVBoxLayout(todos_tab)

        # Grupo: Lista de TODOs
        list_group = QGroupBox("Lista de TODOs")
        list_layout = QVBoxLayout()

        self.todos_list = QListWidget()
        self.todos_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.todos_list.itemDoubleClicked.connect(self._edit_todo)
        self.todos_list.itemClicked.connect(self._on_todo_selected)
        list_layout.addWidget(self.todos_list)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Grupo: Adicionar/Editar TODO
        edit_group = QGroupBox("Adicionar/Editar TODO")
        edit_layout = QFormLayout()

        self.todo_title_edit = QLineEdit()
        self.todo_title_edit.setPlaceholderText("Título do TODO")
        edit_layout.addRow("Título:", self.todo_title_edit)

        self.todo_description_edit = QTextEdit()
        self.todo_description_edit.setMaximumHeight(60)
        self.todo_description_edit.setPlaceholderText("Descrição (opcional)")
        edit_layout.addRow("Descrição:", self.todo_description_edit)

        self.todo_recurring_check = QCheckBox("TODO Recorrente (diário)")
        self.todo_recurring_check.toggled.connect(self._on_recurring_toggled)
        edit_layout.addRow(self.todo_recurring_check)

        self.todo_time_edit = QTimeEdit()
        self.todo_time_edit.setDisplayFormat("HH:mm")
        self.todo_time_edit.setTime(QTime(9, 0))  # Default 9:00 AM
        self.todo_time_edit.setEnabled(False)
        edit_layout.addRow("Horário agendado:", self.todo_time_edit)

        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)

        # Botões
        btn_layout = QHBoxLayout()

        self.add_todo_btn = QPushButton("Adicionar")
        self.add_todo_btn.clicked.connect(self._add_todo)
        btn_layout.addWidget(self.add_todo_btn)

        self.update_todo_btn = QPushButton("Atualizar Selecionado")
        self.update_todo_btn.clicked.connect(self._update_todo)
        self.update_todo_btn.setEnabled(False)
        btn_layout.addWidget(self.update_todo_btn)

        remove_btn = QPushButton("Remover")
        remove_btn.clicked.connect(self._remove_todo)
        btn_layout.addWidget(remove_btn)

        self.clear_form_btn = QPushButton("Limpar")
        self.clear_form_btn.clicked.connect(self._clear_todo_form)
        btn_layout.addWidget(self.clear_form_btn)

        layout.addLayout(btn_layout)

        # Dica
        tip_label = QLabel("TODOs recorrentes exigem código de 8 caracteres para conclusão.\n"
                          "Duplo clique para editar um TODO.")
        tip_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(tip_label)

        layout.addStretch()

        # Carrega TODOs existentes
        self._load_todos()

        return todos_tab

    def _on_recurring_toggled(self, checked: bool):
        """Habilita/desabilita seleção de horário baseado em recorrência."""
        self.todo_time_edit.setEnabled(checked)

    def _load_todos(self):
        """Carrega TODOs na lista."""
        self.todos_list.clear()
        for todo in self._todos:
            status_icon = "[OK]" if todo.status == TodoStatus.COMPLETED.value else "[  ]"
            recurring_icon = "[R]" if todo.is_recurring else ""
            time_str = f" {todo.scheduled_time}" if todo.scheduled_time else ""
            display_text = f"{status_icon} {recurring_icon} {todo.title}{time_str}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, todo.id)
            self.todos_list.addItem(item)

    def _on_todo_selected(self, item: QListWidgetItem):
        """Habilita botão de atualizar quando um TODO é selecionado."""
        self.update_todo_btn.setEnabled(True)

    def _add_todo(self):
        """Adiciona um novo TODO."""
        title = self.todo_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Aviso", "O título é obrigatório.")
            return

        todo = TodoItem(
            title=title,
            description=self.todo_description_edit.toPlainText().strip(),
            is_recurring=self.todo_recurring_check.isChecked(),
            scheduled_time=self.todo_time_edit.time().toString("HH:mm") if self.todo_recurring_check.isChecked() else None
        )

        self._todos.append(todo)
        self._load_todos()
        self._clear_todo_form()

    def _update_todo(self):
        """Atualiza o TODO selecionado."""
        current_item = self.todos_list.currentItem()
        if not current_item:
            return

        title = self.todo_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Aviso", "O título é obrigatório.")
            return

        todo_id = current_item.data(Qt.ItemDataRole.UserRole)
        for todo in self._todos:
            if todo.id == todo_id:
                todo.title = title
                todo.description = self.todo_description_edit.toPlainText().strip()
                todo.is_recurring = self.todo_recurring_check.isChecked()
                todo.scheduled_time = self.todo_time_edit.time().toString("HH:mm") if todo.is_recurring else None
                break

        self._load_todos()
        self._clear_todo_form()

    def _remove_todo(self):
        """Remove o TODO selecionado."""
        current_item = self.todos_list.currentItem()
        if not current_item:
            return

        todo_id = current_item.data(Qt.ItemDataRole.UserRole)
        self._todos = [t for t in self._todos if t.id != todo_id]
        self._load_todos()
        self._clear_todo_form()

    def _edit_todo(self, item: QListWidgetItem):
        """Carrega TODO selecionado no formulário para edição."""
        todo_id = item.data(Qt.ItemDataRole.UserRole)
        for todo in self._todos:
            if todo.id == todo_id:
                self.todo_title_edit.setText(todo.title)
                self.todo_description_edit.setPlainText(todo.description)
                self.todo_recurring_check.setChecked(todo.is_recurring)
                if todo.scheduled_time:
                    h, m = map(int, todo.scheduled_time.split(':'))
                    self.todo_time_edit.setTime(QTime(h, m))
                self._editing_todo_id = todo_id
                self.update_todo_btn.setEnabled(True)
                break

    def _clear_todo_form(self):
        """Limpa o formulário de TODO."""
        self.todo_title_edit.clear()
        self.todo_description_edit.clear()
        self.todo_recurring_check.setChecked(False)
        self.todo_time_edit.setTime(QTime(9, 0))
        self._editing_todo_id = None
        self.update_todo_btn.setEnabled(False)
        self.todos_list.clearSelection()

    def get_todos(self) -> List[TodoItem]:
        """Retorna a lista de TODOs editada."""
        return self._todos.copy()

    def get_settings(self) -> AppSettings:
        """Retorna as configurações editadas."""
        self.settings.break_interval = self.break_interval_spin.value()
        self.settings.break_duration = self.break_duration_spin.value()
        self.settings.show_pre_notification = self.pre_notify_check.isChecked()
        self.settings.pre_notification_seconds = self.pre_notify_spin.value()
        self.settings.play_sound = self.play_sound_check.isChecked()
        self.settings.allow_skip = self.allow_skip_check.isChecked()
        self.settings.allow_postpone = self.allow_postpone_check.isChecked()
        self.settings.postpone_minutes = self.postpone_spin.value()
        self.settings.start_minimized = self.start_minimized_check.isChecked()
        self.settings.start_with_windows = self.start_windows_check.isChecked()
        self.settings.water_reminder_interval = self.water_reminder_spin.value()

        # Coleta mensagens da lista
        self.settings.break_messages = []
        for i in range(self.messages_list.count()):
            self.settings.break_messages.append(self.messages_list.item(i).text())

        return self.settings


class WsiBreakTimeApp:
    """Aplicação principal Wsi Break Time."""

    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings

        # Componentes
        self.timer = TimerManager()
        self.tray = TrayIcon()
        self.overlay = BreakOverlay()
        self.multi_overlay = MultiScreenOverlay()

        # TODO Manager
        self.todo_manager = TodoManager()
        self.todo_manager.set_todos(self.settings_manager.get_todos())

        # Timer para atualizar status no tray
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_tray_status)
        self.status_timer.setInterval(1000)

        self._connect_signals()
        self._apply_settings()

    def _connect_signals(self):
        """Conecta os sinais entre componentes."""
        # Timer -> App
        self.timer.break_started.connect(self._on_break_started)
        self.timer.break_ended.connect(self._on_break_ended)
        self.timer.tick.connect(self._on_break_tick)
        self.timer.pre_notification.connect(self._on_pre_notification)
        self.timer.water_reminder.connect(self._on_water_reminder)

        # Tray -> App
        self.tray.show_settings_requested.connect(self._show_settings)
        self.tray.pause_requested.connect(self._pause_timer)
        self.tray.resume_requested.connect(self._resume_timer)
        self.tray.skip_requested.connect(self._skip_break)
        self.tray.take_break_now_requested.connect(self._take_break_now)
        self.tray.quit_requested.connect(self._quit)

        # Overlay -> App
        self.overlay.skip_requested.connect(self._skip_break)
        self.overlay.postpone_requested.connect(self._postpone_break)

        # TodoManager -> App
        self.todo_manager.todo_due.connect(self._on_todo_due)
        self.todo_manager.todos_changed.connect(self._on_todos_changed)
        self.todo_manager.verification_required.connect(self._on_verification_required)

        # Tray -> App (TODOs)
        self.tray.complete_todo_requested.connect(self._on_complete_todo_requested)

    def _apply_settings(self):
        """Aplica as configurações ao timer e overlay."""
        self.timer.configure(
            break_interval=self.settings.break_interval,
            break_duration=self.settings.break_duration,
            pre_notification_seconds=self.settings.pre_notification_seconds if self.settings.show_pre_notification else 0,
            water_interval=self.settings.water_reminder_interval
        )

    def _get_random_message(self) -> str:
        """Retorna uma mensagem aleatória da lista."""
        if self.settings.break_messages:
            return random.choice(self.settings.break_messages)
        return "Hora de descansar!"

    def start(self):
        """Inicia a aplicação."""
        self.tray.show()
        self.timer.start()
        self.todo_manager.start()
        self.status_timer.start()

        # Atualiza menu de TODOs
        self._on_todos_changed()

        # Notificação inicial
        self.tray.show_notification(
            "Wsi Break Time Iniciado",
            f"Próxima pausa em {self.settings.break_interval} minutos.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def _update_tray_status(self):
        """Atualiza o status no menu do tray."""
        if not self.timer.is_on_break:
            remaining = self.timer.get_time_until_break()
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            self.tray.update_status(f"{minutes:02d}:{seconds:02d}")

    def _on_break_started(self):
        """Chamado quando uma pausa inicia."""
        self.tray.set_break_state(True)

        # Seleciona mensagem aleatória e configura overlay
        random_message = self._get_random_message()
        self.overlay.configure(
            message=random_message,
            duration=self.settings.break_duration,
            allow_skip=self.settings.allow_skip,
            allow_postpone=self.settings.allow_postpone,
            postpone_minutes=self.settings.postpone_minutes
        )
        self.overlay.show_fullscreen()

    def _on_break_ended(self):
        """Chamado quando uma pausa termina."""
        self.overlay.close()
        self.tray.set_break_state(False)

    def _on_break_tick(self, seconds_remaining: int):
        """Atualiza o contador durante a pausa."""
        self.overlay.update_countdown(seconds_remaining)

    def _on_pre_notification(self, seconds: int):
        """Notifica que a pausa está próxima."""
        self.tray.show_notification(
            "Pausa em breve",
            f"Sua pausa começará em {seconds} segundos.",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    def _on_water_reminder(self):
        """Lembrete de beber água."""
        self.tray.show_notification(
            "Hora de hidratar!",
            "Beba um copo de água para manter-se hidratado.",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    def _show_settings(self):
        """Abre o diálogo de configurações."""
        dialog = SettingsDialog(
            self.settings,
            self.timer,
            todos=self.todo_manager.get_todos()
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            self.settings_manager.settings = self.settings
            self.settings_manager.save()
            self._apply_settings()

            # Atualiza TODOs
            self.todo_manager.set_todos(dialog.get_todos())
            self.settings_manager.save_todos(self.todo_manager.get_todos())

            # Reinicia o timer com novas configurações
            was_running = self.timer.is_running
            self.timer.stop()
            if was_running:
                self.timer.start()

    def _pause_timer(self):
        """Pausa o timer."""
        self.timer.pause()
        self.tray.set_paused_state(True)
        self.status_timer.stop()

    def _resume_timer(self):
        """Retoma o timer."""
        self.timer.resume()
        self.tray.set_paused_state(False)
        self.status_timer.start()

    def _skip_break(self):
        """Pula a pausa atual."""
        self.timer.skip_break()
        self.overlay.close()

    def _postpone_break(self, minutes: int):
        """Adia a pausa."""
        self.timer.postpone_break(minutes)
        self.overlay.close()

        self.tray.show_notification(
            "Pausa adiada",
            f"Próxima pausa em {minutes} minutos.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def _take_break_now(self):
        """Inicia uma pausa imediatamente."""
        self.timer.main_timer.stop()
        self.timer.pre_notify_timer.stop()
        self.timer._start_break()

    def _quit(self):
        """Encerra a aplicação."""
        self.timer.stop()
        self.todo_manager.stop()
        self.status_timer.stop()
        self.overlay.close()
        self.tray.hide()
        QApplication.quit()

    def _on_todo_due(self, todo: TodoItem):
        """Chamado quando um TODO está pendente no horário."""
        time_str = f" - {todo.scheduled_time}" if todo.scheduled_time else ""
        recurring_str = " (recorrente)" if todo.is_recurring else ""
        self.tray.show_notification(
            "TODO Pendente",
            f"{todo.title}{time_str}{recurring_str}",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    def _on_todos_changed(self):
        """Atualiza o menu do tray quando TODOs mudam."""
        pending = self.todo_manager.get_pending_todos()
        self.tray.update_todos_menu(pending)

        # Persiste alterações
        self.settings_manager.save_todos(self.todo_manager.get_todos())

    def _on_verification_required(self, todo: TodoItem, code: str):
        """Exibe diálogo de verificação para TODO recorrente."""
        dialog = TodoVerificationDialog(todo, code)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entered_code = dialog.get_entered_code()
            self.todo_manager.verify_and_complete(todo.id, entered_code)

    def _on_complete_todo_requested(self, todo_id: str):
        """Usuário solicitou completar um TODO via menu do tray."""
        self.todo_manager.request_completion(todo_id)
