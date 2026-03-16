# Timer Manager

> Arquivo fonte: `src/timer_manager.py` (6 KB)

## Propósito

Gerencia os intervalos entre pausas, a contagem regressiva durante as pausas, notificações prévias e lembretes de água. Usa QTimers do Qt para toda a temporização.

## Signals Emitidos

| Signal | Parâmetros | Quando |
|--------|-----------|--------|
| `break_starting` | — | Imediatamente antes da pausa iniciar |
| `break_started` | — | Pausa iniciou (emitido logo após `break_starting`) |
| `break_ended` | — | Pausa terminou (por timeout ou skip) |
| `tick` | `int` (segundos restantes) | A cada segundo durante a pausa |
| `pre_notification` | `int` (segundos até a pausa) | X segundos antes da pausa |
| `water_reminder` | — | Periodicamente, conforme intervalo configurado |

**Nota:** `break_starting` e `break_started` são emitidos em sequência no mesmo momento. Ambos existem para permitir diferentes ações (ex: preparação vs exibição).

## Estado Interno

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `is_running` | `bool` | `False` | Timer está ativo |
| `is_on_break` | `bool` | `False` | Usuário está em pausa |
| `break_seconds_remaining` | `int` | `0` | Countdown da pausa |
| `break_interval` | `int` | `20` | Minutos entre pausas (config) |
| `break_duration` | `int` | `20` | Segundos de pausa (config) |
| `pre_notification_seconds` | `int` | `30` | Antecedência da notificação (config) |
| `water_interval` | `int` | `0` | Minutos entre lembretes de água (config) |
| `next_break_time` | `datetime?` | `None` | Horário calculado da próxima pausa |
| `session_start_time` | `datetime?` | `None` | Início da sessão atual |
| `breaks_taken` | `int` | `0` | Contador de pausas realizadas |

## Timers Internos (QTimer)

| Timer | Tipo | Intervalo | Propósito |
|-------|------|-----------|-----------|
| `main_timer` | single-shot (via start com ms) | `break_interval * 60 * 1000` ms | Dispara quando é hora da pausa |
| `break_timer` | repeating | 1000 ms (1s) | Ticks durante a pausa |
| `pre_notify_timer` | single-shot | `interval_ms - (pre_notification_seconds * 1000)` | Aviso antes da pausa |
| `water_timer` | repeating | `water_interval * 60 * 1000` ms | Lembretes de água |

## Métodos Públicos

### configure(break_interval, break_duration, pre_notification_seconds, water_interval)
Armazena os parâmetros de configuração. Não reinicia timers.

### start()
- Se já rodando, retorna (guard)
- Define `is_running = True`
- Registra `session_start_time = now()`
- Chama `_start_main_timer()` para iniciar contagem
- Se `water_interval > 0`, inicia `water_timer`

### stop()
- Define `is_running = False`
- Para todos os 4 timers
- Define `next_break_time = None`

### pause()
- Somente se `is_running` E `not is_on_break`
- Para `main_timer` e `pre_notify_timer`
- **NÃO para** `break_timer` (não se pode pausar durante uma pausa)

### resume()
- Somente se `is_running` E `not is_on_break`
- Chama `_start_main_timer()` (recalcula próxima pausa a partir de agora)

### skip_break()
- Somente se `is_on_break`
- Chama `_end_break()`

### postpone_break(minutes=5)
- Se `is_on_break`, chama `_end_break()` primeiro
- Para `main_timer` e `pre_notify_timer`
- Inicia `main_timer` com `minutes * 60 * 1000` ms
- Recalcula `next_break_time`
- Se o tempo de adiamento é maior que `pre_notification_seconds`, agenda `pre_notify_timer`

### get_time_until_break() → timedelta
- Se `next_break_time` é None, retorna timedelta(0)
- Calcula diferença entre `next_break_time` e `now()`
- Se negativo, retorna timedelta(0)

### get_session_duration() → timedelta
- Se `session_start_time` é None, retorna timedelta(0)
- Retorna `now() - session_start_time`

## Fluxos

### Fluxo Normal de Pausa

```
start()
  └→ _start_main_timer()
       ├→ main_timer.start(interval_ms)
       ├→ next_break_time = now + interval
       └→ pre_notify_timer.start(interval_ms - pre_seconds*1000)
              │
              ▼ (pre_notification_seconds antes da pausa)
       _on_pre_notify()
         └→ emit pre_notification(seconds)
              │
              ▼ (hora da pausa)
       _on_main_timer_timeout()
         └→ main_timer.stop()
            _start_break()
              ├→ is_on_break = True
              ├→ break_seconds_remaining = break_duration
              ├→ emit break_starting()
              ├→ emit break_started()
              └→ break_timer.start() [1s interval]
                    │
                    ▼ (a cada segundo)
              _on_break_timer_tick()
                ├→ break_seconds_remaining -= 1
                ├→ emit tick(remaining)
                └→ if remaining <= 0: _end_break()
                      │
                      ▼
              _end_break()
                ├→ break_timer.stop()
                ├→ is_on_break = False
                ├→ breaks_taken += 1
                ├→ emit break_ended()
                └→ if is_running: _start_main_timer() [reinicia ciclo]
```

### Fluxo de Postpone

```
postpone_break(minutes)
  ├→ if is_on_break: _end_break()
  ├→ main_timer.stop()
  ├→ pre_notify_timer.stop()
  ├→ main_timer.start(minutes * 60 * 1000)
  ├→ next_break_time = now + minutes
  └→ if minutes*60 > pre_notification_seconds:
       pre_notify_timer.start(delay_ms - pre_seconds*1000)
```

### Fluxo de Pause/Resume

```
pause()
  ├→ main_timer.stop()
  └→ pre_notify_timer.stop()
  [break_timer NÃO é parado]

resume()
  └→ _start_main_timer()
     [recalcula próxima pausa a partir de agora]
```

**Nota:** Ao resumir, o timer recomeça do zero (não mantém o tempo restante antes da pausa). Isso é intencional — o usuário recebe o intervalo completo após retomar.
