# Configurações e Persistência

> Arquivo fonte: `src/settings.py` (3 KB)

## AppSettings (Dataclass)

Estrutura de dados que armazena todas as preferências do usuário.

### Campos

| Campo | Tipo | Default | Range | Descrição |
|-------|------|---------|-------|-----------|
| `break_interval` | `int` | `20` | 1-120 | Minutos entre pausas |
| `break_duration` | `int` | `20` | 5-300 | Segundos de duração da pausa |
| `break_messages` | `List[str]` | 5 mensagens | min 1 | Mensagens exibidas durante a pausa |
| `start_minimized` | `bool` | `True` | — | Iniciar minimizado no tray |
| `start_with_windows` | `bool` | `False` | — | Iniciar junto com o Windows |
| `show_pre_notification` | `bool` | `True` | — | Exibir notificação antes da pausa |
| `pre_notification_seconds` | `int` | `30` | 5-120 | Segundos de antecedência da notificação |
| `allow_skip` | `bool` | `True` | — | Permitir pular pausas |
| `allow_postpone` | `bool` | `True` | — | Permitir adiar pausas |
| `postpone_minutes` | `int` | `5` | 1-30 | Minutos de adiamento |
| `water_reminder_interval` | `int` | `0` | 0-120 | Minutos entre lembretes de água (0=desativado) |
| `play_sound` | `bool` | `False` | — | Tocar som de alerta |
| `todos` | `List[dict]` | `[]` | — | Lista de TODOs serializados |
| `pomodoro_work_duration` | `int` | `25` | 1-120 | Minutos de trabalho no Pomodoro |
| `pomodoro_short_break` | `int` | `5` | 1-60 | Minutos da pausa curta do Pomodoro |
| `pomodoro_long_break` | `int` | `15` | 1-120 | Minutos da pausa longa do Pomodoro |
| `pomodoro_cycles_before_long` | `int` | `4` | 2-10 | Ciclos antes da pausa longa |

### Mensagens Padrão de Pausa

```
1. "Hora de descansar os olhos!\nOlhe para algo a 6 metros de distância."
2. "Levante-se e alongue o corpo!"
3. "Respire fundo e relaxe os ombros."
4. "Pisque os olhos várias vezes para hidratá-los."
5. "Olhe pela janela e descanse a visão."
```

## SettingsManager

Gerencia a persistência das configurações em arquivo JSON.

### Inicialização

```
config_path = None → %APPDATA%/WsiBreakTime/config.json
config_path = str  → caminho customizado (para testes)
```

- Na inicialização, cria um `AppSettings` com defaults e chama `load()`
- Se o arquivo não existir, usa defaults
- Se houver erro de parsing JSON ou IO, loga no console e mantém defaults

### Métodos

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `load()` | `AppSettings` | Lê config.json, aplica valores aos campos existentes do settings (ignora campos desconhecidos) |
| `save()` | `bool` | Cria diretório se necessário, salva como JSON indentado com UTF-8. Retorna True/False |
| `reset_to_defaults()` | — | Recria AppSettings com defaults e salva |
| `get_todos()` | `List[TodoItem]` | Converte `settings.todos` (dicts) em objetos `TodoItem` via `TodoItem.from_dict()` |
| `save_todos(todos)` | — | Converte `List[TodoItem]` em dicts via `to_dict()`, salva no settings e persiste |

### Formato do config.json

```json
{
  "break_interval": 20,
  "break_duration": 20,
  "break_messages": [
    "Hora de descansar os olhos!\nOlhe para algo a 6 metros de distância.",
    "Levante-se e alongue o corpo!",
    "Respire fundo e relaxe os ombros.",
    "Pisque os olhos várias vezes para hidratá-los.",
    "Olhe pela janela e descanse a visão."
  ],
  "start_minimized": true,
  "start_with_windows": false,
  "show_pre_notification": true,
  "pre_notification_seconds": 30,
  "allow_skip": true,
  "allow_postpone": true,
  "postpone_minutes": 5,
  "water_reminder_interval": 0,
  "play_sound": false,
  "todos": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Revisar relatório",
      "description": "Revisão diária do relatório de vendas",
      "is_recurring": true,
      "scheduled_time": "09:00",
      "status": "pending",
      "completed_at": null,
      "last_reset_date": "2026-03-15",
      "created_at": "2026-01-10T08:30:00.000000"
    }
  ],
  "pomodoro_work_duration": 25,
  "pomodoro_short_break": 5,
  "pomodoro_long_break": 15,
  "pomodoro_cycles_before_long": 4
}
```

### Comportamento de load()

- Lê o arquivo JSON e itera sobre suas chaves
- Para cada chave, verifica se existe como atributo em `AppSettings` via `hasattr()`
- Aplica o valor com `setattr()` — isso permite adicionar novos campos sem quebrar configs antigas
- Campos desconhecidos no JSON são silenciosamente ignorados
- Campos ausentes no JSON mantêm o valor default do dataclass
