"""
Modelo de dados para TODOs recorrentes.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class TodoStatus(Enum):
    """Status de um TODO."""
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """Representa um item TODO."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    is_recurring: bool = False
    scheduled_time: Optional[str] = None  # Format: "HH:MM" for recurring TODOs
    status: str = TodoStatus.PENDING.value
    completed_at: Optional[str] = None  # ISO format datetime
    last_reset_date: Optional[str] = None  # ISO format date (YYYY-MM-DD)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Converte para dicionario para serialização JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TodoItem':
        """Cria instância a partir de dicionário."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_due(self) -> bool:
        """Verifica se o TODO está pendente no horário atual."""
        if self.status != TodoStatus.PENDING.value:
            return False

        if not self.is_recurring or not self.scheduled_time:
            return True

        now = datetime.now()
        scheduled_hour, scheduled_minute = map(int, self.scheduled_time.split(':'))
        scheduled = now.replace(hour=scheduled_hour, minute=scheduled_minute, second=0, microsecond=0)

        # Is it past the scheduled time today?
        return now >= scheduled

    def needs_reset(self) -> bool:
        """Verifica se o TODO recorrente precisa ser resetado para novo dia."""
        if not self.is_recurring:
            return False

        today = datetime.now().date().isoformat()
        return self.last_reset_date != today

    def reset_for_new_day(self):
        """Reseta o TODO para o novo dia."""
        self.status = TodoStatus.PENDING.value
        self.completed_at = None
        self.last_reset_date = datetime.now().date().isoformat()

    def mark_completed(self):
        """Marca o TODO como completo."""
        self.status = TodoStatus.COMPLETED.value
        self.completed_at = datetime.now().isoformat()
