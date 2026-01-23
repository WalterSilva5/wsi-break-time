"""
Módulo de gerenciamento do Pomodoro.
Controla os ciclos de trabalho e pausas no modo Pomodoro.
"""

from enum import Enum
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class PomodoroState(Enum):
    """Estados possíveis do Pomodoro."""
    IDLE = "idle"
    WORKING = "working"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    WAITING_CONFIRMATION = "waiting"


class PomodoroManager(QObject):
    """Gerenciador do modo Pomodoro."""

    # Sinais
    state_changed = pyqtSignal(str)
    tick = pyqtSignal(int)
    cycle_completed = pyqtSignal(int)
    confirmation_needed = pyqtSignal(str)  # Mensagem descritiva
    reminder_notification = pyqtSignal()
    pomodoro_started = pyqtSignal()
    pomodoro_ended = pyqtSignal()
    break_started = pyqtSignal()
    break_ended = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Timers
        self.work_timer = QTimer(self)
        self.work_timer.timeout.connect(self._on_work_timer_tick)
        self.work_timer.setInterval(1000)

        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self._on_break_timer_tick)
        self.break_timer.setInterval(1000)

        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._on_reminder_timer)
        self.reminder_timer.setInterval(30 * 1000)  # 30 segundos

        # Estado
        self._state = PomodoroState.IDLE
        self._cycles_completed = 0
        self._seconds_remaining = 0
        self._waiting_for_work = False  # True se aguardando confirmação para TRABALHO

        # Configurações (valores padrão)
        self.work_duration = 25  # minutos
        self.short_break_duration = 5  # minutos
        self.long_break_duration = 15  # minutos
        self.cycles_before_long_break = 4

    def configure(self, work_duration: int, short_break_duration: int,
                  long_break_duration: int, cycles_before_long_break: int):
        """Configura os parâmetros do Pomodoro."""
        self.work_duration = work_duration
        self.short_break_duration = short_break_duration
        self.long_break_duration = long_break_duration
        self.cycles_before_long_break = cycles_before_long_break

    @property
    def state(self) -> PomodoroState:
        """Retorna o estado atual."""
        return self._state

    @property
    def cycles_completed(self) -> int:
        """Retorna o número de ciclos completados."""
        return self._cycles_completed

    @property
    def seconds_remaining(self) -> int:
        """Retorna os segundos restantes no timer atual."""
        return self._seconds_remaining

    @property
    def is_active(self) -> bool:
        """Retorna True se o Pomodoro está ativo (não IDLE)."""
        return self._state != PomodoroState.IDLE

    def start(self):
        """Inicia o Pomodoro (começa período de trabalho)."""
        if self._state != PomodoroState.IDLE:
            return

        self._cycles_completed = 0
        self._waiting_for_work = False
        self.pomodoro_started.emit()
        self._start_work()

    def stop(self):
        """Encerra completamente o Pomodoro."""
        self.work_timer.stop()
        self.break_timer.stop()
        self.reminder_timer.stop()
        self._set_state(PomodoroState.IDLE)
        self._cycles_completed = 0
        self._seconds_remaining = 0
        self._waiting_for_work = False
        self.pomodoro_ended.emit()

    def confirm_next_cycle(self):
        """Usuário confirma para iniciar o próximo ciclo."""
        if self._state != PomodoroState.WAITING_CONFIRMATION:
            return

        self.reminder_timer.stop()

        if self._waiting_for_work:
            # Após pausa, inicia trabalho
            self._start_work()
        else:
            # Após trabalho, inicia pausa
            self._start_break()

    def end_session(self):
        """Usuário decide encerrar a sessão."""
        self.stop()

    def get_status_text(self) -> str:
        """Retorna texto de status para exibição."""
        if self._state == PomodoroState.IDLE:
            return "Pomodoro inativo"
        elif self._state == PomodoroState.WORKING:
            minutes = self._seconds_remaining // 60
            seconds = self._seconds_remaining % 60
            return f"Trabalho - {minutes:02d}:{seconds:02d}"
        elif self._state == PomodoroState.SHORT_BREAK:
            minutes = self._seconds_remaining // 60
            seconds = self._seconds_remaining % 60
            return f"Pausa curta - {minutes:02d}:{seconds:02d}"
        elif self._state == PomodoroState.LONG_BREAK:
            minutes = self._seconds_remaining // 60
            seconds = self._seconds_remaining % 60
            return f"Pausa longa - {minutes:02d}:{seconds:02d}"
        elif self._state == PomodoroState.WAITING_CONFIRMATION:
            return "Aguardando confirmação"
        return ""

    def _set_state(self, new_state: PomodoroState):
        """Altera o estado e emite sinal."""
        self._state = new_state
        self.state_changed.emit(new_state.value)

    def _start_work(self):
        """Inicia período de trabalho."""
        self._set_state(PomodoroState.WORKING)
        self._seconds_remaining = self.work_duration * 60
        self._waiting_for_work = False
        self.work_timer.start()

    def _start_break(self):
        """Inicia período de pausa (curta ou longa)."""
        # Determina se é pausa longa
        if (self._cycles_completed % self.cycles_before_long_break) == 0 and self._cycles_completed > 0:
            self._set_state(PomodoroState.LONG_BREAK)
            self._seconds_remaining = self.long_break_duration * 60
        else:
            self._set_state(PomodoroState.SHORT_BREAK)
            self._seconds_remaining = self.short_break_duration * 60

        self._waiting_for_work = False
        self.break_started.emit()
        self.break_timer.start()

    def _on_work_timer_tick(self):
        """Chamado a cada segundo durante trabalho."""
        self._seconds_remaining -= 1
        self.tick.emit(self._seconds_remaining)

        if self._seconds_remaining <= 0:
            self.work_timer.stop()
            self._cycles_completed += 1
            self.cycle_completed.emit(self._cycles_completed)
            self._enter_waiting_state(waiting_for_work=False)

    def _on_break_timer_tick(self):
        """Chamado a cada segundo durante pausa."""
        self._seconds_remaining -= 1
        self.tick.emit(self._seconds_remaining)

        if self._seconds_remaining <= 0:
            self.break_timer.stop()
            self.break_ended.emit()
            self._enter_waiting_state(waiting_for_work=True)

    def _enter_waiting_state(self, waiting_for_work: bool):
        """Entra no estado de aguardando confirmação."""
        self._waiting_for_work = waiting_for_work
        self._set_state(PomodoroState.WAITING_CONFIRMATION)

        if waiting_for_work:
            msg = f"Pausa finalizada! Ciclo {self._cycles_completed} de {self.cycles_before_long_break}. " \
                  f"Inicie o próximo período de trabalho ou encerre."
        else:
            # Determina tipo da próxima pausa
            if (self._cycles_completed % self.cycles_before_long_break) == 0:
                pause_type = "longa"
            else:
                pause_type = "curta"
            msg = f"Ciclo {self._cycles_completed} completo! " \
                  f"Inicie a pausa {pause_type} ou encerre o Pomodoro."

        self.confirmation_needed.emit(msg)
        self.reminder_timer.start()

    def _on_reminder_timer(self):
        """Emite lembrete a cada 30 segundos."""
        if self._state == PomodoroState.WAITING_CONFIRMATION:
            self.reminder_notification.emit()
