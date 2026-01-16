"""
Classe principal da aplicação Wsi Break Time.
Integra todos os componentes: timer, tray, overlay e configurações.
"""

import random
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QCheckBox, QTextEdit, QPushButton, QGroupBox,
    QFormLayout, QTabWidget, QWidget, QSystemTrayIcon,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from settings import SettingsManager, AppSettings
from timer_manager import TimerManager
from tray_icon import TrayIcon
from overlay import BreakOverlay, MultiScreenOverlay


class SettingsDialog(QDialog):
    """Diálogo de configurações."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Configurações - Wsi Break Time")
        self.setMinimumSize(500, 550)
        self._setup_ui()
        self._load_settings()

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
        self.status_timer.start()

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
        dialog = SettingsDialog(self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            self.settings_manager.settings = self.settings
            self.settings_manager.save()
            self._apply_settings()

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
        self.status_timer.stop()
        self.overlay.close()
        self.tray.hide()
        QApplication.quit()
