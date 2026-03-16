# System Tray Icon

> Arquivo fonte: `src/tray_icon.py` (11 KB)

## Propósito

Gerencia o ícone na bandeja do sistema (system tray), o menu de contexto com todas as ações do usuário, notificações do sistema e indicação visual de estado através de cores do ícone.

## Signals

| Signal | Parâmetros | Descrição |
|--------|-----------|-----------|
| `show_settings_requested` | — | Abrir dialog de configurações |
| `pause_requested` | — | Pausar o timer |
| `resume_requested` | — | Retomar o timer |
| `skip_requested` | — | Pular pausa atual |
| `take_break_now_requested` | — | Iniciar pausa imediata |
| `quit_requested` | — | Encerrar aplicação |
| `complete_todo_requested` | `str` (todo_id) | Completar um TODO |
| `start_pomodoro_requested` | — | Iniciar modo Pomodoro |
| `confirm_pomodoro_cycle_requested` | — | Confirmar próximo ciclo |
| `end_pomodoro_requested` | — | Encerrar Pomodoro |

## Estado Interno

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `is_paused` | `bool` | `False` | Timer pausado |
| `is_on_break` | `bool` | `False` | Em pausa ativa |
| `pomodoro_active` | `bool` | `False` | Pomodoro ativo |
| `pomodoro_waiting_confirmation` | `bool` | `False` | Aguardando ação do usuário |

## Ícone Dinâmico

O ícone é gerado programaticamente quando `resources/icons/app_icon.ico` não existe.

### Especificação do Ícone

- **Tamanho:** 64x64 pixels (QPixmap)
- **Fundo:** Transparente
- **Círculo:** Preenchido com a cor do estado, raio de 28px (ellipse 4,4 a 56,56)
- **Letra:** "W" centralizada (Arial, 24pt, Bold, branca)
- **Antialiasing:** Ativado

### Cores por Estado

| Estado | Cor | Hex | Tooltip |
|--------|-----|-----|---------|
| Ativo (normal) | Verde | `#4CAF50` | "Wsi Break Time - Ativo" |
| Pausado | Amarelo | `#FFC107` | "Wsi Break Time - Pausado" |
| Em pausa (break) | Azul | `#2196F3` | "Wsi Break Time - Descanse seus olhos" |
| Pomodoro ativo | Rosa/Magenta | `#E91E63` | "Pomodoro - Ativo" |
| Pomodoro aguardando | Laranja | `#FF9800` | "Pomodoro - Aguardando confirmação" |

### Carregamento do Ícone

1. Busca `resources/icons/app_icon.ico` relativo ao diretório pai do arquivo `tray_icon.py`
2. Se existe, usa `QIcon(path)`
3. Se não existe, cria via `_create_default_icon("#4CAF50")`

## Estrutura do Menu de Contexto

```
┌─────────────────────────────────┐
│ Próxima pausa em: MM:SS        │  ← status_action (disabled)
├─────────────────────────────────┤
│ ▸ TODOs Pendentes              │  ← todos_menu (submenu)
│   ├─ [R] TODO título [09:00]   │    items dinâmicos
│   ├─ TODO título               │
│   ├─────────────────────────── │
│   └─ Gerenciar TODOs...        │    → show_settings_requested
├─────────────────────────────────┤
│ Pausar / Retomar               │  ← pause_action (toggle)
│ Fazer pausa agora              │  ← take_break_action
│ Pular pausa                    │  ← skip_action (hidden normalmente)
├─────────────────────────────────┤
│ Iniciar Pomodoro               │  ← start_pomodoro_action (qdo inativo)
│ Iniciar próximo ciclo          │  ← confirm_pomodoro_action (qdo waiting)
│ Encerrar Pomodoro              │  ← end_pomodoro_action (qdo ativo)
├─────────────────────────────────┤
│ Configurações...               │  ← settings_action
├─────────────────────────────────┤
│ Sair                           │  ← quit_action
└─────────────────────────────────┘
```

### Visibilidade dos Itens de Menu

| Item | Visível quando |
|------|----------------|
| `skip_action` | `is_on_break == True` |
| `take_break_action` | `is_on_break == False` |
| `pause_action` | `is_on_break == False` AND `pomodoro_active == False` |
| `start_pomodoro_action` | `pomodoro_active == False` |
| `end_pomodoro_action` | `pomodoro_active == True` |
| `confirm_pomodoro_action` | `pomodoro_active == True` AND `pomodoro_waiting_confirmation == True` |

### TODOs Submenu

- Se não há TODOs pendentes: exibe "Nenhum TODO pendente" (disabled)
- Para cada TODO pendente:
  - Formato: `[R] título [HH:MM]` (onde `[R]` aparece se recorrente, `[HH:MM]` se tem horário)
  - Click emite `complete_todo_requested(todo.id)` via lambda com captura correta do id
- Separador
- "Gerenciar TODOs..." → emite `show_settings_requested`

## Interações

### Double-click no Ícone
`tray_icon.activated` com `ActivationReason.DoubleClick` → emite `show_settings_requested`

### Toggle Pausar/Retomar
`pause_action` tem texto dinâmico:
- Se `is_paused`: texto "Retomar", click → `resume_requested`
- Se não `is_paused`: texto "Pausar", click → `pause_requested`

## Métodos Públicos

| Método | Descrição |
|--------|-----------|
| `show()` | Exibe ícone no tray |
| `hide()` | Esconde ícone do tray |
| `show_notification(title, message, icon, duration_ms)` | Exibe toast notification. Icon padrão: `Information`. Duration padrão: 5000ms |
| `update_status(time_remaining)` | Atualiza texto do status_action: `f"Próxima pausa em: {time_remaining}"` |
| `set_paused_state(paused)` | Atualiza estado visual: texto do botão, cor do ícone, tooltip, texto do status |
| `set_break_state(on_break)` | Mostra/esconde skip/take_break/pause, atualiza cor do ícone para azul |
| `update_todos_menu(pending_todos)` | Reconstrói submenu de TODOs |
| `set_pomodoro_state(active, waiting_confirmation, status_text)` | Atualiza visibilidade dos itens Pomodoro, cor do ícone, texto de status |
| `update_pomodoro_status(status_text)` | Atualiza apenas o texto de status quando Pomodoro ativo |

### Detalhe: set_paused_state(paused)
- Se `paused=True`:
  - Texto: "Retomar"
  - Status: "Timer pausado"
  - Ícone: amarelo `#FFC107`
  - Tooltip: "Wsi Break Time - Pausado"
- Se `paused=False`:
  - Texto: "Pausar"
  - Ícone: verde `#4CAF50`
  - Tooltip: "Wsi Break Time - Ativo"

### Detalhe: set_break_state(on_break)
- Se `on_break=True`:
  - `skip_action` visível
  - `take_break_action` invisível
  - `pause_action` invisível
  - Status: "Em pausa..."
  - Ícone: azul `#2196F3`
  - Tooltip: "Wsi Break Time - Descanse seus olhos"

### Detalhe: set_pomodoro_state(active, waiting_confirmation, status_text)
- `start_pomodoro_action` visível quando `not active`
- `end_pomodoro_action` visível quando `active`
- `confirm_pomodoro_action` visível quando `active and waiting_confirmation`
- `pause_action` e `take_break_action` invisíveis quando `active`
- Se `active and waiting_confirmation`: ícone laranja `#FF9800`
- Se `active and not waiting_confirmation`: ícone rosa `#E91E63`
- Se `not active`: ícone verde `#4CAF50`
