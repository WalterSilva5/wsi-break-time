# Pomodoro Manager

> Arquivo fonte: `src/pomodoro_manager.py` (8 KB)

## Propósito

Implementa a técnica Pomodoro — ciclos alternados de trabalho focado e pausas. Quando ativo, substitui o timer regular de pausas.

## PomodoroState (Enum)

```
IDLE                  = "idle"       → Inativo
WORKING               = "working"   → Período de trabalho
SHORT_BREAK           = "short_break" → Pausa curta
LONG_BREAK            = "long_break"  → Pausa longa
WAITING_CONFIRMATION  = "waiting"    → Aguardando ação do usuário
```

## Signals

| Signal | Parâmetros | Descrição |
|--------|-----------|-----------|
| `state_changed` | `str` (valor do enum) | Estado mudou |
| `tick` | `int` (segundos restantes) | A cada segundo durante trabalho ou pausa |
| `cycle_completed` | `int` (número do ciclo) | Ciclo de trabalho completado |
| `confirmation_needed` | `str` (mensagem descritiva) | Precisa ação do usuário |
| `reminder_notification` | — | Lembrete a cada 30s durante espera |
| `pomodoro_started` | — | Pomodoro foi iniciado |
| `pomodoro_ended` | — | Pomodoro foi encerrado |
| `break_started` | — | Pausa (curta ou longa) iniciou |
| `break_ended` | — | Pausa terminou |

## Configuração

| Parâmetro | Default | Range (UI) | Descrição |
|-----------|---------|------------|-----------|
| `work_duration` | 25 min | 1-120 | Duração do período de trabalho |
| `short_break_duration` | 5 min | 1-60 | Duração da pausa curta |
| `long_break_duration` | 15 min | 1-120 | Duração da pausa longa |
| `cycles_before_long_break` | 4 | 2-10 | Ciclos antes da pausa longa |

## Estado Interno

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `_state` | `PomodoroState` | `IDLE` | Estado atual |
| `_cycles_completed` | `int` | `0` | Ciclos de trabalho completados |
| `_seconds_remaining` | `int` | `0` | Countdown atual |
| `_waiting_for_work` | `bool` | `False` | Se True, próximo ciclo é trabalho; se False, próximo é pausa |

## Timers

| Timer | Intervalo | Propósito |
|-------|-----------|-----------|
| `work_timer` | 1000 ms | Ticks durante período de trabalho |
| `break_timer` | 1000 ms | Ticks durante pausa |
| `reminder_timer` | 30.000 ms | Lembrete repetido em WAITING_CONFIRMATION |

## State Machine

```
                    start()
                      │
                      ▼
    ┌─────────────────────────────────┐
    │           WORKING               │
    │  _seconds_remaining = work*60   │
    │  work_timer rodando (1s ticks)  │
    └─────────────┬───────────────────┘
                  │ _seconds_remaining == 0
                  │ cycles_completed += 1
                  │ cycle_completed(n) emitido
                  ▼
    ┌─────────────────────────────────┐
    │    WAITING_CONFIRMATION         │◄──────────────┐
    │    _waiting_for_work = False    │               │
    │    reminder_timer (30s)         │               │
    │                                 │               │
    │    msg: "Ciclo N completo!      │               │
    │    Inicie a pausa {tipo}"       │               │
    └─────────────┬───────────────────┘               │
                  │ confirm_next_cycle()              │
                  ▼                                   │
    ┌─────────────────────────────────┐               │
    │      SHORT_BREAK / LONG_BREAK   │               │
    │  (depende de cycles_completed)  │               │
    │  break_timer rodando (1s ticks) │               │
    │  break_started emitido          │               │
    └─────────────┬───────────────────┘               │
                  │ _seconds_remaining == 0           │
                  │ break_ended emitido               │
                  ▼                                   │
    ┌─────────────────────────────────┐               │
    │    WAITING_CONFIRMATION         │               │
    │    _waiting_for_work = True     │               │
    │    reminder_timer (30s)         │               │
    │                                 │               │
    │    msg: "Pausa finalizada!      │               │
    │    Inicie o próximo trabalho"   │               │
    └─────────────┬───────────────────┘               │
                  │ confirm_next_cycle()              │
                  │                                   │
                  └───────► WORKING ──────────────────┘

    stop() em qualquer estado → IDLE
```

## Lógica de Pausa Curta vs Longa

```python
if (cycles_completed % cycles_before_long_break) == 0 and cycles_completed > 0:
    → LONG_BREAK (long_break_duration * 60 segundos)
else:
    → SHORT_BREAK (short_break_duration * 60 segundos)
```

**Exemplo com cycles_before_long_break = 4:**
- Ciclo 1 → short break
- Ciclo 2 → short break
- Ciclo 3 → short break
- Ciclo 4 → **long break** (4 % 4 == 0 && 4 > 0)
- Ciclo 5 → short break
- Ciclo 8 → **long break**

## Métodos Públicos

### start()
- Guard: se não está IDLE, retorna
- Reseta `_cycles_completed = 0`
- Reseta `_waiting_for_work = False`
- Emite `pomodoro_started`
- Chama `_start_work()`

### stop()
- Para todos os 3 timers
- Define estado para IDLE
- Reseta contadores
- Emite `pomodoro_ended`

### confirm_next_cycle()
- Guard: se não está em WAITING_CONFIRMATION, retorna
- Para `reminder_timer`
- Se `_waiting_for_work == True` → `_start_work()` (após pausa, volta a trabalhar)
- Se `_waiting_for_work == False` → `_start_break()` (após trabalho, inicia pausa)

### get_status_text() → str
Retorna texto legível para exibição no tray:
- IDLE: `"Pomodoro inativo"`
- WORKING: `"Trabalho - MM:SS"`
- SHORT_BREAK: `"Pausa curta - MM:SS"`
- LONG_BREAK: `"Pausa longa - MM:SS"`
- WAITING_CONFIRMATION: `"Aguardando confirmação"`

### Properties
- `state` → PomodoroState
- `cycles_completed` → int
- `seconds_remaining` → int
- `is_active` → bool (True se estado != IDLE)

## Mensagens de Confirmação

### Após trabalho (_waiting_for_work = False):
```
"Ciclo {N} completo! Inicie a pausa {curta/longa} ou encerre o Pomodoro."
```
Onde `{curta/longa}` é determinado pela mesma lógica de pausa curta vs longa.

### Após pausa (_waiting_for_work = True):
```
"Pausa finalizada! Ciclo {N} de {cycles_before_long_break}. Inicie o próximo período de trabalho ou encerre."
```

## Integração com Timer Regular

Quando o Pomodoro é ativado:
1. O orquestrador pausa o `TimerManager` regular (`timer.pause()`)
2. Para o `status_timer` do tray
3. O Pomodoro assume o controle do tray status

Quando o Pomodoro é encerrado:
1. O orquestrador retoma o `TimerManager` (`timer.resume()`)
2. Reinicia o `status_timer`
3. Reseta estado visual do tray para verde
