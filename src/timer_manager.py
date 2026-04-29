"""
Módulo de gerenciamento de timer.
Controla os intervalos entre pausas e os lembretes de confirmação de sessão.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime, timedelta


class TimerManager(QObject):
    """Gerenciador de timers para controle das pausas."""

    break_starting = pyqtSignal()
    break_started = pyqtSignal()
    break_ended = pyqtSignal()
    pre_notification = pyqtSignal(int)
    water_reminder = pyqtSignal()
    confirmation_reminder = pyqtSignal()

    REMINDER_INTERVAL_MS = 60 * 1000  # 1 minuto

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self._on_main_timer_timeout)

        self.pre_notify_timer = QTimer(self)
        self.pre_notify_timer.timeout.connect(self._on_pre_notify)
        self.pre_notify_timer.setSingleShot(True)

        self.water_timer = QTimer(self)
        self.water_timer.timeout.connect(self._on_water_reminder)

        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._on_reminder)
        self.reminder_timer.setInterval(self.REMINDER_INTERVAL_MS)

        self.is_running = False
        self.is_on_break = False

        self.break_interval = 20
        self.pre_notification_seconds = 30
        self.water_interval = 0

        self.next_break_time: datetime = None
        self.session_start_time: datetime = None
        self.breaks_taken = 0

    def configure(self, break_interval: int,
                  pre_notification_seconds: int = 30, water_interval: int = 0):
        """Configura os intervalos do timer."""
        self.break_interval = break_interval
        self.pre_notification_seconds = pre_notification_seconds
        self.water_interval = water_interval

    def start(self):
        """Inicia o timer de pausas."""
        if self.is_running:
            return

        self.is_running = True
        self.session_start_time = datetime.now()
        self._start_main_timer()

        if self.water_interval > 0:
            self.water_timer.start(self.water_interval * 60 * 1000)

    def stop(self):
        """Para todos os timers."""
        self.is_running = False
        self.main_timer.stop()
        self.pre_notify_timer.stop()
        self.water_timer.stop()
        self.reminder_timer.stop()
        self.next_break_time = None

    def pause(self):
        """Pausa o timer (mantém o estado)."""
        if self.is_running and not self.is_on_break:
            self.main_timer.stop()
            self.pre_notify_timer.stop()

    def resume(self):
        """Retoma o timer pausado."""
        if self.is_running and not self.is_on_break:
            self._start_main_timer()

    def confirm_break(self):
        """Confirma a sessão e encerra a pausa atual."""
        if self.is_on_break:
            self._end_break()

    def get_time_until_break(self) -> timedelta:
        """Retorna o tempo restante até a próxima pausa."""
        if self.next_break_time is None:
            return timedelta(0)
        remaining = self.next_break_time - datetime.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def get_session_duration(self) -> timedelta:
        """Retorna a duração da sessão atual."""
        if self.session_start_time is None:
            return timedelta(0)
        return datetime.now() - self.session_start_time

    def _start_main_timer(self):
        """Inicia o timer principal."""
        interval_ms = self.break_interval * 60 * 1000
        self.main_timer.start(interval_ms)
        self.next_break_time = datetime.now() + timedelta(minutes=self.break_interval)

        if self.pre_notification_seconds > 0 and self.break_interval * 60 > self.pre_notification_seconds:
            pre_notify_delay = interval_ms - (self.pre_notification_seconds * 1000)
            self.pre_notify_timer.start(pre_notify_delay)

    def _on_main_timer_timeout(self):
        """Chamado quando é hora de fazer uma pausa."""
        self.main_timer.stop()
        self._start_break()

    def _on_pre_notify(self):
        """Chamado segundos antes da pausa."""
        self.pre_notification.emit(self.pre_notification_seconds)

    def _start_break(self):
        """Inicia uma pausa."""
        self.is_on_break = True
        self.break_starting.emit()
        self.break_started.emit()
        self.reminder_timer.start()

    def _end_break(self):
        """Finaliza a pausa."""
        self.reminder_timer.stop()
        self.is_on_break = False
        self.breaks_taken += 1
        self.break_ended.emit()

        if self.is_running:
            self._start_main_timer()

    def _on_reminder(self):
        """Emite lembrete de confirmação de sessão."""
        self.confirmation_reminder.emit()

    def _on_water_reminder(self):
        """Emite lembrete de beber água."""
        self.water_reminder.emit()
