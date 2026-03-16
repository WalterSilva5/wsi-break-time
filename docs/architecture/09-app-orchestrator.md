# App Orchestrator (WsiBreakTimeApp)

> Arquivo fonte: `src/app.py` — classe `WsiBreakTimeApp` (linhas 679-1038)

## Propósito

Classe principal que instancia todos os componentes, conecta seus signals e coordena todas as interações. **Não é um QObject** — é uma classe Python simples.

## Componentes Criados

| Componente | Classe | Variável |
|------------|--------|----------|
| Settings | `SettingsManager` | `self.settings_manager` |
| Config | `AppSettings` | `self.settings` |
| Timer | `TimerManager` | `self.timer` |
| Tray | `TrayIcon` | `self.tray` |
| Overlay | `BreakOverlay` | `self.overlay` |
| Multi Overlay | `MultiScreenOverlay` | `self.multi_overlay` |
| TODOs | `TodoManager` | `self.todo_manager` |
| Pomodoro | `PomodoroManager` | `self.pomodoro` |
| Status Timer | `QTimer` (1s) | `self.status_timer` |

## Inicialização

```
__init__()
  ├→ SettingsManager() → carrega config.json
  ├→ TimerManager()
  ├→ TrayIcon()
  ├→ BreakOverlay()
  ├→ MultiScreenOverlay()
  ├→ TodoManager() → set_todos(settings_manager.get_todos())
  ├→ PomodoroManager()
  ├→ QTimer (status_timer, 1s) → _update_tray_status
  ├→ _connect_signals()
  └→ _apply_settings()
```

## Mapa de Signal/Slot Connections

### TimerManager → WsiBreakTimeApp

| Signal | Slot | Ação |
|--------|------|------|
| `break_started` | `_on_break_started` | Configura e exibe overlay fullscreen |
| `break_ended` | `_on_break_ended` | Fecha overlay, reseta estado do tray |
| `tick(int)` | `_on_break_tick` | Atualiza countdown no overlay |
| `pre_notification(int)` | `_on_pre_notification` | Exibe notificação "Pausa em breve" |
| `water_reminder` | `_on_water_reminder` | Exibe notificação de hidratação |

### TrayIcon → WsiBreakTimeApp

| Signal | Slot | Ação |
|--------|------|------|
| `show_settings_requested` | `_show_settings` | Abre SettingsDialog |
| `pause_requested` | `_pause_timer` | Pausa timer + atualiza visual |
| `resume_requested` | `_resume_timer` | Retoma timer + atualiza visual |
| `skip_requested` | `_skip_break` | Pula pausa + fecha overlay |
| `take_break_now_requested` | `_take_break_now` | Inicia pausa imediata |
| `quit_requested` | `_quit` | Encerra aplicação |
| `complete_todo_requested(str)` | `_on_complete_todo_requested` | Solicita conclusão de TODO |
| `start_pomodoro_requested` | `_start_pomodoro` | Inicia Pomodoro |
| `confirm_pomodoro_cycle_requested` | `_confirm_pomodoro_cycle` | Confirma próximo ciclo |
| `end_pomodoro_requested` | `_end_pomodoro` | Encerra Pomodoro |

### BreakOverlay → WsiBreakTimeApp

| Signal | Slot | Ação |
|--------|------|------|
| `skip_requested` | `_skip_break` | Pula pausa + fecha overlay |
| `postpone_requested(int)` | `_postpone_break` | Adia pausa + fecha overlay + notificação |

### TodoManager → WsiBreakTimeApp

| Signal | Slot | Ação |
|--------|------|------|
| `todo_due(object)` | `_on_todo_due` | Exibe notificação com título do TODO |
| `todos_changed` | `_on_todos_changed` | Atualiza menu do tray + persiste |
| `verification_required(object, str)` | `_on_verification_required` | Exibe TodoVerificationDialog |

### PomodoroManager → WsiBreakTimeApp

| Signal | Slot | Ação |
|--------|------|------|
| `state_changed(str)` | `_on_pomodoro_state_changed` | Atualiza estado visual no tray |
| `tick(int)` | `_on_pomodoro_tick` | Atualiza status text no tray |
| `confirmation_needed(str)` | `_on_pomodoro_confirmation_needed` | Notificação com mensagem descritiva (10s) |
| `reminder_notification` | `_on_pomodoro_reminder` | Notificação warning "Clique no ícone..." (5s) |
| `pomodoro_started` | `_on_pomodoro_started` | Notificação "Pomodoro Iniciado" + visual tray |
| `pomodoro_ended` | `_on_pomodoro_ended` | Notificação "Pomodoro Encerrado" + reset tray |
| `break_started` | `_on_pomodoro_break_started` | Notificação "Pausa curta/longa" |
| `break_ended` | `_on_pomodoro_break_ended` | (pass — tratado via confirmation_needed) |

---

## Fluxos Detalhados

### Startup (start)

```
start()
  ├→ tray.show()
  ├→ timer.start()
  ├→ todo_manager.start()
  ├→ status_timer.start()
  ├→ _on_todos_changed()  [atualiza menu de TODOs]
  └→ tray.show_notification(
       "Wsi Break Time Iniciado",
       "Próxima pausa em {interval} minutos.",
       Information, 3000ms)
```

### Shutdown (_quit)

```
_quit()
  ├→ timer.stop()
  ├→ todo_manager.stop()
  ├→ status_timer.stop()
  ├→ overlay.close()
  ├→ tray.hide()
  └→ QApplication.quit()
```

### Break Flow

```
_on_break_started()
  ├→ tray.set_break_state(True)
  ├→ _get_random_message() → seleciona mensagem aleatória
  ├→ overlay.configure(message, duration, allow_skip, allow_postpone, postpone_minutes)
  └→ overlay.show_fullscreen()

_on_break_tick(seconds_remaining)
  └→ overlay.update_countdown(seconds_remaining)

_on_break_ended()
  ├→ overlay.close()
  └→ tray.set_break_state(False)

_skip_break()
  ├→ timer.skip_break()
  └→ overlay.close()

_postpone_break(minutes)
  ├→ timer.postpone_break(minutes)
  ├→ overlay.close()
  └→ tray.show_notification("Pausa adiada", "Próxima pausa em {minutes} minutos.", 3000ms)

_take_break_now()
  ├→ timer.main_timer.stop()    [acesso direto ao timer interno]
  ├→ timer.pre_notify_timer.stop()
  └→ timer._start_break()       [acesso direto ao método privado]
```

### Settings Flow

```
_show_settings()
  ├→ SettingsDialog(settings, timer, todos=todo_manager.get_todos())
  ├→ if dialog.exec() == Accepted:
  │   ├→ settings = dialog.get_settings()
  │   ├→ settings_manager.settings = settings
  │   ├→ settings_manager.save()
  │   ├→ _apply_settings()  [reconfigura timer e pomodoro]
  │   ├→ todo_manager.set_todos(dialog.get_todos())
  │   ├→ settings_manager.save_todos(todo_manager.get_todos())
  │   ├→ was_running = timer.is_running
  │   ├→ timer.stop()
  │   └→ if was_running: timer.start()  [reinicia com novas configs]
```

### Pause/Resume

```
_pause_timer()
  ├→ timer.pause()
  ├→ tray.set_paused_state(True)
  └→ status_timer.stop()

_resume_timer()
  ├→ timer.resume()
  ├→ tray.set_paused_state(False)
  └→ status_timer.start()
```

### TODO Completion Flow

```
_on_complete_todo_requested(todo_id)
  └→ todo_manager.request_completion(todo_id)
       ├→ [não recorrente] → completa direto → emite todo_completed + todos_changed
       └→ [recorrente] → gera código → emite verification_required

_on_verification_required(todo, code)
  ├→ TodoVerificationDialog(todo, code)
  └→ if dialog.exec() == Accepted:
       └→ todo_manager.verify_and_complete(todo.id, dialog.get_entered_code())

_on_todos_changed()
  ├→ pending = todo_manager.get_pending_todos()
  ├→ tray.update_todos_menu(pending)
  └→ settings_manager.save_todos(todo_manager.get_todos())
```

### Pomodoro Flow

```
_start_pomodoro()
  ├→ Guard: if pomodoro.is_active → return
  ├→ timer.pause()       [pausa timer regular]
  ├→ status_timer.stop()
  └→ pomodoro.start()

_end_pomodoro()
  ├→ pomodoro.stop()
  ├→ timer.resume()      [retoma timer regular]
  ├→ tray.set_paused_state(False)
  └→ status_timer.start()

_confirm_pomodoro_cycle()
  └→ pomodoro.confirm_next_cycle()
```

### Tray Status Update

```
_update_tray_status()  [chamado a cada 1s pelo status_timer]
  ├→ if pomodoro.is_active → return  [Pomodoro tem seu próprio status]
  └→ if not timer.is_on_break:
       ├→ remaining = timer.get_time_until_break()
       └→ tray.update_status("MM:SS")
```

---

## _apply_settings()

Chamado na inicialização e após salvar configurações:

```
_apply_settings()
  ├→ timer.configure(
  │     break_interval = settings.break_interval,
  │     break_duration = settings.break_duration,
  │     pre_notification_seconds = settings.pre_notification_seconds if show_pre_notification else 0,
  │     water_interval = settings.water_reminder_interval
  │   )
  └→ pomodoro.configure(
        work_duration = settings.pomodoro_work_duration,
        short_break_duration = settings.pomodoro_short_break,
        long_break_duration = settings.pomodoro_long_break,
        cycles_before_long_break = settings.pomodoro_cycles_before_long
      )
```

**Nota:** Se `show_pre_notification == False`, passa `pre_notification_seconds = 0` ao timer, efetivamente desabilitando a pré-notificação (o timer só agenda pré-notify se `pre_notification_seconds > 0`).

---

## Notificações do Sistema

| Evento | Título | Mensagem | Ícone | Duração |
|--------|--------|----------|-------|---------|
| Startup | "Wsi Break Time Iniciado" | "Próxima pausa em {N} minutos." | Information | 3s |
| Pré-pausa | "Pausa em breve" | "Sua pausa começará em {N} segundos." | Information | 5s |
| Água | "Hora de hidratar!" | "Beba um copo de água para manter-se hidratado." | Information | 5s |
| Postpone | "Pausa adiada" | "Próxima pausa em {N} minutos." | Information | 3s |
| TODO due | "TODO Pendente" | "{título} - {hora} (recorrente)" | Information | 5s |
| Pomodoro início | "Pomodoro Iniciado" | "Período de trabalho: {N} minutos. Foco!" | Information | 3s |
| Pomodoro fim | "Pomodoro Encerrado" | "Você completou {N} ciclo(s). Bom trabalho!" | Information | 3s |
| Pomodoro ação | "Pomodoro - Ação Necessária" | (mensagem dinâmica) | Information | 10s |
| Pomodoro lembrete | "Pomodoro Aguardando" | "Clique no ícone do tray..." | Warning | 5s |
| Pomodoro pausa curta | "Pomodoro - Pausa" | "Pausa curta! Relaxe um pouco." | Information | 3s |
| Pomodoro pausa longa | "Pomodoro - Pausa" | "Pausa longa! Descanse bem." | Information | 3s |
