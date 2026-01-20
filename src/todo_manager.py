"""
Módulo de gerenciamento de TODOs recorrentes.
Controla a criação, edição, verificação e reset diário de TODOs.
"""

import random
import string
from datetime import datetime, timedelta
from typing import List, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from todo_model import TodoItem, TodoStatus


class TodoManager(QObject):
    """Gerenciador de TODOs recorrentes."""

    # Signals
    todo_due = pyqtSignal(object)  # Emitted when a TODO becomes due (TodoItem)
    todo_completed = pyqtSignal(object)  # Emitted when a TODO is completed (TodoItem)
    todos_changed = pyqtSignal()  # Emitted when the todo list changes
    verification_required = pyqtSignal(object, str)  # Emitted with TODO and verification code

    def __init__(self, parent=None):
        super().__init__(parent)

        self._todos: List[TodoItem] = []
        self._notified_todos: set = set()  # Track which TODOs have been notified today

        # Timer to check for due TODOs and daily resets (every minute)
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self._check_todos)
        self._check_timer.setInterval(60 * 1000)  # 60 seconds

        # Timer for midnight reset check
        self._midnight_timer = QTimer(self)
        self._midnight_timer.timeout.connect(self._check_midnight_reset)
        self._midnight_timer.setSingleShot(True)

        self._pending_verification: dict[str, str] = {}  # todo_id -> verification_code

    def start(self):
        """Inicia o gerenciador de TODOs."""
        self._check_todos()  # Initial check
        self._check_timer.start()
        self._schedule_midnight_reset()

    def stop(self):
        """Para o gerenciador de TODOs."""
        self._check_timer.stop()
        self._midnight_timer.stop()

    def set_todos(self, todos: List[TodoItem]):
        """Define a lista de TODOs (usado para carregar do settings)."""
        self._todos = todos
        self._notified_todos.clear()
        self._check_todos()  # Check immediately

    def get_todos(self) -> List[TodoItem]:
        """Retorna todos os TODOs."""
        return self._todos.copy()

    def get_pending_todos(self) -> List[TodoItem]:
        """Retorna TODOs pendentes que estão no horário."""
        return [t for t in self._todos if t.is_due()]

    def get_recurring_todos(self) -> List[TodoItem]:
        """Retorna TODOs recorrentes."""
        return [t for t in self._todos if t.is_recurring]

    def add_todo(self, todo: TodoItem):
        """Adiciona um novo TODO."""
        self._todos.append(todo)
        self.todos_changed.emit()

    def remove_todo(self, todo_id: str):
        """Remove um TODO pelo ID."""
        self._todos = [t for t in self._todos if t.id != todo_id]
        if todo_id in self._pending_verification:
            del self._pending_verification[todo_id]
        self._notified_todos.discard(todo_id)
        self.todos_changed.emit()

    def update_todo(self, todo: TodoItem):
        """Atualiza um TODO existente."""
        for i, t in enumerate(self._todos):
            if t.id == todo.id:
                self._todos[i] = todo
                break
        self.todos_changed.emit()

    def request_completion(self, todo_id: str) -> Optional[str]:
        """
        Solicita completar um TODO recorrente.
        Gera e retorna código de verificação para TODOs recorrentes.
        Para TODOs não-recorrentes, completa diretamente.
        """
        todo = self._get_todo_by_id(todo_id)
        if not todo:
            return None

        if todo.is_recurring:
            # Generate 8-character alphanumeric code
            code = self._generate_verification_code()
            self._pending_verification[todo_id] = code
            self.verification_required.emit(todo, code)
            return code
        else:
            # Non-recurring TODO: complete directly
            self._complete_todo(todo)
            return None

    def verify_and_complete(self, todo_id: str, entered_code: str) -> bool:
        """
        Verifica o código e completa o TODO se correto.
        Retorna True se verificação bem-sucedida, False caso contrário.
        """
        if todo_id not in self._pending_verification:
            return False

        expected_code = self._pending_verification[todo_id]
        if entered_code.upper() == expected_code.upper():
            todo = self._get_todo_by_id(todo_id)
            if todo:
                self._complete_todo(todo)
                del self._pending_verification[todo_id]
                return True
        return False

    def _generate_verification_code(self) -> str:
        """Gera código alfanumérico de 8 caracteres."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=8))

    def _complete_todo(self, todo: TodoItem):
        """Marca TODO como completo."""
        todo.mark_completed()
        self._notified_todos.discard(todo.id)
        self.todo_completed.emit(todo)
        self.todos_changed.emit()

    def _get_todo_by_id(self, todo_id: str) -> Optional[TodoItem]:
        """Busca TODO pelo ID."""
        for todo in self._todos:
            if todo.id == todo_id:
                return todo
        return None

    def _check_todos(self):
        """Verifica TODOs pendentes e reseta recorrentes se necessário."""
        for todo in self._todos:
            # Reset recurring TODOs for new day
            if todo.needs_reset():
                todo.reset_for_new_day()
                self._notified_todos.discard(todo.id)
                self.todos_changed.emit()

            # Emit signal for due TODOs (only once per day)
            if todo.is_due() and todo.id not in self._notified_todos:
                self._notified_todos.add(todo.id)
                self.todo_due.emit(todo)

    def _schedule_midnight_reset(self):
        """Agenda verificação para meia-noite."""
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=1, microsecond=0
        )
        ms_until_midnight = int((tomorrow - now).total_seconds() * 1000)
        self._midnight_timer.start(ms_until_midnight)

    def _check_midnight_reset(self):
        """Reseta TODOs recorrentes à meia-noite."""
        self._notified_todos.clear()
        for todo in self._todos:
            if todo.is_recurring:
                todo.reset_for_new_day()
        self.todos_changed.emit()
        self._schedule_midnight_reset()  # Schedule next midnight
