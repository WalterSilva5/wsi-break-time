# Sistema de TODOs

> Arquivos fonte: `src/todo_model.py` (2 KB), `src/todo_manager.py` (7 KB)

## Propósito

Permite ao usuário criar tarefas (TODOs) que podem ser únicas ou recorrentes diárias. TODOs recorrentes exigem digitação de um código de verificação de 8 caracteres para confirmação, evitando conclusões acidentais.

---

## TodoStatus (Enum)

```
PENDING   = "pending"
COMPLETED = "completed"
```

---

## TodoItem (Dataclass)

### Campos

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `id` | `str` | `uuid4()` | Identificador único (gerado automaticamente) |
| `title` | `str` | `""` | Título da tarefa (obrigatório na UI) |
| `description` | `str` | `""` | Descrição opcional |
| `is_recurring` | `bool` | `False` | Se True, reseta diariamente |
| `scheduled_time` | `str?` | `None` | Horário agendado no formato `"HH:MM"` (apenas para recorrentes) |
| `status` | `str` | `"pending"` | Valor do enum TodoStatus |
| `completed_at` | `str?` | `None` | Data/hora de conclusão (ISO 8601) |
| `last_reset_date` | `str?` | `None` | Data do último reset diário (formato `"YYYY-MM-DD"`) |
| `created_at` | `str` | `now().isoformat()` | Data/hora de criação (ISO 8601) |

### Métodos

#### to_dict() → dict
Usa `dataclasses.asdict()` para serialização JSON.

#### from_dict(data) → TodoItem (classmethod)
Filtra o dict para incluir apenas chaves que existem nos campos do dataclass, ignorando chaves desconhecidas. Isso garante compatibilidade forward se novos campos forem adicionados.

#### is_due() → bool
Determina se o TODO está pendente e pronto para notificação:
1. Se `status != "pending"` → False
2. Se `not is_recurring` ou `not scheduled_time` → True (TODOs simples sempre due quando pending)
3. Se recorrente com horário: compara `now()` com o horário agendado no dia atual
   - Parse: `scheduled_time.split(':')` → hour, minute
   - Cria datetime com hora/minuto do agendamento no dia atual
   - Retorna `now >= scheduled`

#### needs_reset() → bool
Verifica se um TODO recorrente precisa ser resetado para o novo dia:
1. Se `not is_recurring` → False
2. Compara `last_reset_date` com `today.isoformat()` (formato "YYYY-MM-DD")
3. Se diferentes → True (precisa reset)

#### reset_for_new_day()
- `status = "pending"`
- `completed_at = None`
- `last_reset_date = today.isoformat()`

#### mark_completed()
- `status = "completed"`
- `completed_at = now().isoformat()`

---

## TodoManager (QObject)

### Signals

| Signal | Parâmetros | Descrição |
|--------|-----------|-----------|
| `todo_due` | `object` (TodoItem) | TODO está pendente no horário |
| `todo_completed` | `object` (TodoItem) | TODO foi completado |
| `todos_changed` | — | Lista de TODOs foi modificada |
| `verification_required` | `object, str` (TodoItem, código) | TODO recorrente precisa verificação |

### Estado Interno

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `_todos` | `List[TodoItem]` | Lista completa de TODOs |
| `_notified_todos` | `set` | IDs de TODOs já notificados hoje (dedup) |
| `_pending_verification` | `dict[str, str]` | Mapa `todo_id → verification_code` |

### Timers

| Timer | Tipo | Intervalo | Propósito |
|-------|------|-----------|-----------|
| `_check_timer` | repeating | 60.000 ms (1 min) | Verifica TODOs due e resets |
| `_midnight_timer` | single-shot | ms até 00:00:01 | Reset à meia-noite |

### Métodos Públicos

#### start()
- Executa `_check_todos()` imediatamente
- Inicia `_check_timer` (60s)
- Agenda `_schedule_midnight_reset()`

#### stop()
Para ambos os timers.

#### set_todos(todos: List[TodoItem])
- Substitui lista interna
- Limpa `_notified_todos`
- Executa `_check_todos()` imediatamente

#### get_todos() → List[TodoItem]
Retorna cópia da lista (`.copy()`).

#### get_pending_todos() → List[TodoItem]
Retorna TODOs onde `is_due() == True`.

#### get_recurring_todos() → List[TodoItem]
Retorna TODOs onde `is_recurring == True`.

#### add_todo(todo) / remove_todo(todo_id) / update_todo(todo)
CRUD básico. Cada operação emite `todos_changed`.
`remove_todo` também limpa `_pending_verification` e `_notified_todos` para o ID.

#### request_completion(todo_id) → Optional[str]
Fluxo de conclusão:
1. Busca TODO por ID
2. Se não encontrado → `None`
3. Se **recorrente**:
   - Gera código de 8 caracteres
   - Armazena em `_pending_verification[todo_id]`
   - Emite `verification_required(todo, code)`
   - Retorna código
4. Se **não recorrente**:
   - Completa diretamente via `_complete_todo()`
   - Retorna `None`

#### verify_and_complete(todo_id, entered_code) → bool
1. Se `todo_id` não está em `_pending_verification` → False
2. Compara `entered_code.upper()` com `expected_code.upper()` (case-insensitive)
3. Se match:
   - Completa o TODO
   - Remove de `_pending_verification`
   - Retorna True
4. Se não match → False

### Código de Verificação

- **Caracteres:** `A-Z` + `0-9` (uppercase + dígitos)
- **Tamanho:** 8 caracteres
- **Geração:** `random.choices(chars, k=8)`
- **Comparação:** Case-insensitive (`upper()` em ambos os lados)

### Lógica de Verificação Periódica (_check_todos)

Executada a cada 60 segundos:

```
Para cada TODO:
  1. Se needs_reset():
     - reset_for_new_day()
     - Remove do _notified_todos
     - Emite todos_changed
  2. Se is_due() E id NOT in _notified_todos:
     - Adiciona id ao _notified_todos
     - Emite todo_due(todo)
```

### Reset à Meia-Noite

#### _schedule_midnight_reset()
- Calcula milissegundos até 00:00:01 do dia seguinte
- Agenda `_midnight_timer` como single-shot

#### _check_midnight_reset()
- Limpa `_notified_todos`
- Para cada TODO recorrente: `reset_for_new_day()`
- Emite `todos_changed`
- Reagenda via `_schedule_midnight_reset()` (para a próxima meia-noite)

---

## TodoVerificationDialog (QDialog)

> Definido em `src/app.py`

### Propósito
Dialog modal que exibe o código de verificação e solicita que o usuário o digite para confirmar a conclusão de um TODO recorrente.

### Construtor
`TodoVerificationDialog(todo: TodoItem, verification_code: str, parent=None)`

### Dimensões
- Mínimo: 400x280 pixels

### Layout Visual

```
┌──────────────────────────────────────┐
│    Completar: {todo.title}           │
│    (Segoe UI, 14pt, Bold, center)    │
│                                      │
│    {todo.description}                │
│    (gray, wordWrap) [se existir]     │
│                                      │
│  ┌─ Digite o código abaixo ────────┐ │
│  │                                  │ │
│  │        AB12CD34                  │ │
│  │  (Consolas, 24pt, Bold, center)  │ │
│  │  (bg: #f0f0f0, border: #ccc)    │ │
│  │  (letter-spacing: 5px)          │ │
│  │                                  │ │
│  │  [_________________________]     │ │
│  │  (Consolas, 16pt, maxLength=8)   │ │
│  │  placeholder: "Digite o código"  │ │
│  └──────────────────────────────────┘ │
│                                      │
│              [Cancelar] [Confirmar]  │
│                                      │
└──────────────────────────────────────┘
```

### Comportamento
- **Botão Confirmar:** Desabilitado até que 8 caracteres sejam digitados
- **Validação:** Compara `input.upper()` com `code.upper()`
- **Código correto:** `accept()` (fecha dialog com sucesso)
- **Código incorreto:** `QMessageBox.warning("Código Incorreto", "O código digitado não confere. Tente novamente.")`, limpa input, foca no campo
- **Cancelar:** `reject()` (fecha dialog sem ação)
- **get_entered_code():** Retorna texto digitado (usado pelo orquestrador após accept)
