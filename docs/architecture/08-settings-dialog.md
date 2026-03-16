# Settings Dialog

> Arquivo fonte: `src/app.py` — classe `SettingsDialog` (linhas 117-677)

## Propósito

Dialog modal com 5 abas para configurar todos os aspectos da aplicação. Inclui visualização em tempo real do próximo horário de pausa.

## Construtor

```python
SettingsDialog(
    settings: AppSettings,           # Configurações atuais
    timer_manager: TimerManager?,    # Para exibir próxima pausa (opcional)
    todos: List[TodoItem]?,          # Lista de TODOs (opcional)
    parent=None
)
```

## Dimensões

- **Mínimo:** 500x600 pixels
- **Título:** "Configurações - Wsi Break Time"

## Timer de Atualização

Se `timer_manager` é fornecido:
- `update_timer` (QTimer, 1s) atualiza informações da próxima pausa a cada segundo
- Parado automaticamente no `closeEvent()`

---

## Aba 1: Pausas

### Grupo: Intervalo
| Widget | Tipo | Range | Sufixo | Label |
|--------|------|-------|--------|-------|
| `break_interval_spin` | QSpinBox | 1-120 | " minutos" | "Pausa a cada:" |
| `break_duration_spin` | QSpinBox | 5-300 | " segundos" | "Duração da pausa:" |

### Grupo: Próxima Pausa (condicional — só se timer_manager fornecido)
| Widget | Tipo | Font | Label |
|--------|------|------|-------|
| `next_break_time_label` | QLabel | Arial 14pt Bold | "Horário:" |
| `time_remaining_label` | QLabel | Arial 12pt | "Tempo restante:" |

**Lógica de atualização (`_update_next_break_info`):**
- Se timer não rodando: "Timer pausado" / "--:--"
- Se em pausa: "Em pausa agora" / "--:--"
- Se ativo: horário `HH:MM:SS` / `MM:SS` restante

### Grupo: Notificações
| Widget | Tipo | Range | Descrição |
|--------|------|-------|-----------|
| `pre_notify_check` | QCheckBox | — | "Notificar antes da pausa" |
| `pre_notify_spin` | QSpinBox | 5-120 | Sufixo: " segundos antes" |
| `play_sound_check` | QCheckBox | — | "Tocar som de alerta" |

### Grupo: Controles
| Widget | Tipo | Range | Descrição |
|--------|------|-------|-----------|
| `allow_skip_check` | QCheckBox | — | "Permitir pular pausas" |
| `allow_postpone_check` | QCheckBox | — | "Permitir adiar pausas" |
| `postpone_spin` | QSpinBox | 1-30 | Sufixo: " minutos" |

---

## Aba 2: Mensagens

### Layout
- **Label:** "Mensagens exibidas durante a pausa (seleção aleatória):"
- **QListWidget** (`messages_list`): seleção única, double-click para editar
- **QTextEdit** (`message_edit`): max height 80px, placeholder "Digite uma nova mensagem aqui..."
- **Botões:** Adicionar | Atualizar Selecionada | Remover
- **Dica:** "Dica: Duplo clique em uma mensagem para editá-la" (gray, 11px)

### Comportamento
- **Adicionar:** Pega texto do message_edit, se não vazio adiciona à lista, limpa o campo
- **Atualizar:** Substitui texto do item selecionado pelo texto do message_edit
- **Remover:** Remove item selecionado. Se é o último, exibe warning: "Deve haver pelo menos uma mensagem na lista." (mínimo 1 mensagem)
- **Double-click:** Carrega texto da mensagem selecionada no message_edit

---

## Aba 3: Geral

### Grupo: Inicialização
| Widget | Tipo | Descrição |
|--------|------|-----------|
| `start_minimized_check` | QCheckBox | "Iniciar minimizado" |
| `start_windows_check` | QCheckBox | "Iniciar com o Windows" |

### Grupo: Extras
| Widget | Tipo | Range | Descrição |
|--------|------|-------|-----------|
| `water_reminder_spin` | QSpinBox | 0-120 | Sufixo: " minutos", specialValueText: "Desativado" (quando 0) |

---

## Aba 4: TODOs

### Grupo: Lista de TODOs
- **QListWidget** (`todos_list`): seleção única
- Double-click → `_edit_todo()`
- Click → `_on_todo_selected()` (habilita botão Atualizar)

**Formato do item na lista:**
```
{status_icon} {recurring_icon} {title}{time_str}
```
- `status_icon`: `"[OK]"` se completed, `"[  ]"` se pending
- `recurring_icon`: `"[R]"` se recorrente, `""` se não
- `time_str`: `" HH:MM"` se tem scheduled_time, `""` se não
- Cada item armazena `todo.id` em `Qt.ItemDataRole.UserRole`

### Grupo: Adicionar/Editar TODO
| Widget | Tipo | Descrição |
|--------|------|-----------|
| `todo_title_edit` | QLineEdit | Placeholder: "Título do TODO" |
| `todo_description_edit` | QTextEdit | Max height 60px, placeholder: "Descrição (opcional)" |
| `todo_recurring_check` | QCheckBox | "TODO Recorrente (diário)" — toggle habilita time_edit |
| `todo_time_edit` | QTimeEdit | Formato "HH:mm", default 09:00, desabilitado até recurring checked |

### Botões
| Botão | Comportamento |
|-------|---------------|
| Adicionar | Valida título obrigatório, cria TodoItem, adiciona à lista, limpa form |
| Atualizar Selecionado | Atualiza campos do TODO selecionado (desabilitado até seleção) |
| Remover | Remove TODO selecionado da lista |
| Limpar | Limpa formulário, deseleciona lista, desabilita Atualizar |

### Dica
"TODOs recorrentes exigem código de 8 caracteres para conclusão.\nDuplo clique para editar um TODO." (gray, 11px)

---

## Aba 5: Pomodoro

### Grupo: Durações
| Widget | Tipo | Range | Sufixo | Label |
|--------|------|-------|--------|-------|
| `pomodoro_work_spin` | QSpinBox | 1-120 | " minutos" | "Trabalho:" |
| `pomodoro_short_break_spin` | QSpinBox | 1-60 | " minutos" | "Pausa curta:" |
| `pomodoro_long_break_spin` | QSpinBox | 1-120 | " minutos" | "Pausa longa:" |
| `pomodoro_cycles_spin` | QSpinBox | 2-10 | — | "Ciclos antes da pausa longa:" |

**Nota:** Os valores são carregados diretamente dos settings no construtor (não em `_load_settings()`).

### Grupo: Como funciona
Texto informativo (gray, wordWrap):
```
O Pomodoro é uma técnica de produtividade que alterna períodos de trabalho
focado com pausas curtas. Após um número de ciclos, uma pausa longa é feita.

1. Inicie o Pomodoro pelo menu do tray
2. Trabalhe durante o período configurado
3. Ao final, confirme para iniciar a pausa ou encerrar
4. Se não confirmar, lembretes serão exibidos a cada 30 segundos
```

---

## Botões Principais

| Botão | Ação |
|-------|------|
| Cancelar | `reject()` — fecha sem salvar |
| Salvar | `accept()` — fecha com sucesso (isDefault=True) |

---

## Métodos de Retorno

### get_settings() → AppSettings
Coleta valores de todos os widgets e atualiza o objeto `self.settings`:
- Todos os spinboxes, checkboxes
- Mensagens da lista (itera `messages_list.count()`)
- Valores do Pomodoro
- Retorna o objeto settings atualizado

### get_todos() → List[TodoItem]
Retorna cópia da lista interna de TODOs (`self._todos.copy()`).
