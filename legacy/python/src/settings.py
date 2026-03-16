"""
Módulo de configurações do Wsi Break Time.
Gerencia o carregamento e salvamento das preferências do usuário.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List


DEFAULT_MESSAGES = [
    "Hora de descansar os olhos!\nOlhe para algo a 6 metros de distância.",
    "Levante-se e alongue o corpo!",
    "Respire fundo e relaxe os ombros.",
    "Pisque os olhos várias vezes para hidratá-los.",
    "Olhe pela janela e descanse a visão.",
]


@dataclass
class AppSettings:
    """Configurações da aplicação."""

    break_interval: int = 20
    break_duration: int = 20
    break_messages: List[str] = field(default_factory=lambda: DEFAULT_MESSAGES.copy())
    start_minimized: bool = True
    start_with_windows: bool = False
    show_pre_notification: bool = True
    pre_notification_seconds: int = 30
    allow_skip: bool = True
    allow_postpone: bool = True
    postpone_minutes: int = 5
    water_reminder_interval: int = 0
    play_sound: bool = False
    todos: List[dict] = field(default_factory=list)  # Lista de TODOs serializados

    # Configurações do Pomodoro
    pomodoro_work_duration: int = 25  # minutos
    pomodoro_short_break: int = 5  # minutos
    pomodoro_long_break: int = 15  # minutos
    pomodoro_cycles_before_long: int = 4  # ciclos antes da pausa longa


class SettingsManager:
    """Gerenciador de configurações."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            app_data = os.getenv('APPDATA', os.path.expanduser('~'))
            self.config_dir = Path(app_data) / 'WsiBreakTime'
            self.config_path = self.config_dir / 'config.json'
        else:
            self.config_path = Path(config_path)
            self.config_dir = self.config_path.parent

        self.settings = AppSettings()
        self.load()

    def load(self) -> AppSettings:
        """Carrega as configurações do arquivo."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar configurações: {e}")

        return self.settings

    def save(self) -> bool:
        """Salva as configurações no arquivo."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Erro ao salvar configurações: {e}")
            return False

    def reset_to_defaults(self):
        """Restaura as configurações padrão."""
        self.settings = AppSettings()
        self.save()

    def get_todos(self) -> list:
        """Retorna a lista de TODOs como objetos TodoItem."""
        from todo_model import TodoItem
        return [TodoItem.from_dict(d) for d in self.settings.todos]

    def save_todos(self, todos: list):
        """Salva a lista de TODOs."""
        self.settings.todos = [t.to_dict() for t in todos]
        self.save()
