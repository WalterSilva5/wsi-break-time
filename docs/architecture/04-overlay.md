# Overlay Fullscreen

> Arquivo fonte: `src/overlay.py` (10 KB)

## Propósito

Exibe uma tela escura fullscreen durante as pausas, com mensagem motivacional, contagem regressiva e botões de controle. Suporta múltiplos monitores.

---

## BreakOverlay (QWidget)

### Window Flags

```python
Qt.WindowType.FramelessWindowHint |
Qt.WindowType.WindowStaysOnTopHint |
Qt.WindowType.Tool
```

- **FramelessWindowHint** — Sem barra de título e bordas
- **WindowStaysOnTopHint** — Sempre acima de outras janelas
- **Tool** — Não aparece na taskbar

### Atributo

```python
WA_TranslucentBackground = False
```

### Signals

| Signal | Parâmetros | Descrição |
|--------|-----------|-----------|
| `skip_requested` | — | Usuário clicou "Pular" ou pressionou ESC |
| `postpone_requested` | `int` (minutos) | Usuário clicou "Adiar X min" |

### Estado Interno

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `allow_skip` | `bool` | `True` | Botão pular visível |
| `allow_postpone` | `bool` | `True` | Botão adiar visível |
| `postpone_minutes` | `int` | `5` | Minutos de adiamento |
| `break_message` | `str` | (mensagem padrão) | Texto exibido |
| `break_duration` | `int` | `20` | Duração total em segundos |

### Design Visual

```
┌─────────────────────────────────────────────────────────┐
│                  (fundo rgba(0,0,0,230))                │
│                                                         │
│              Pausa para os olhos                        │
│         (Segoe UI, 36pt, Light, white)                  │
│                                                         │
│          Hora de descansar os olhos!                     │
│    Olhe para algo a 6 metros de distância.              │
│         (Segoe UI, 18pt, #B0B0B0, wordWrap)             │
│                                                         │
│                       15                                │
│         (Segoe UI, 72pt, Bold, #4CAF50)                 │
│         (muda para #FF9800 quando <= 5s)                │
│                                                         │
│              segundos restantes                         │
│           (Segoe UI, 14pt, #808080)                     │
│                                                         │
│         ████████████░░░░░░░░ (progress bar)             │
│         (300-400px largura, 8px altura)                  │
│         (fundo: #333333, chunk: #4CAF50)                │
│         (border-radius: 4px)                            │
│                                                         │
│         [  Pular  ]    [ Adiar 5 min ]                  │
│         (#424242)       (#1565C0)                       │
│         (120x40)        (140x40)                        │
│         (border-radius: 20px)                           │
│                                                         │
│           Pressione ESC para pular                      │
│           (Segoe UI, 10pt, #505050)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Estilos dos Botões

**Botão Pular:**
- Normal: `background-color: #424242; color: white; border-radius: 20px; padding: 10px 30px`
- Hover: `#616161`
- Pressed: `#757575`

**Botão Adiar:**
- Normal: `background-color: #1565C0; color: white; border-radius: 20px; padding: 10px 30px`
- Hover: `#1976D2`
- Pressed: `#1E88E5`

### Métodos

#### configure(message, duration, allow_skip, allow_postpone, postpone_minutes)
Chamado antes de exibir. Configura:
- Texto da mensagem
- Progress bar: maximum = duration, value = duration
- Visibilidade dos botões skip e postpone
- Texto do botão postpone: `f"Adiar {postpone_minutes} min"`

#### update_countdown(seconds_remaining)
Chamado a cada segundo durante a pausa:
- Atualiza texto do countdown label
- Atualiza valor da progress bar
- Se `seconds_remaining <= 5`: cor do countdown muda para `#FF9800` (laranja)
- Caso contrário: cor mantém `#4CAF50` (verde)

#### show_fullscreen()
- Obtém geometria da tela principal via `QApplication.primaryScreen()`
- Define geometria do widget para cobrir toda a tela
- Reseta countdown label para `break_duration`
- Reseta progress bar para `break_duration`
- Reseta cor do countdown para verde
- Chama `showFullScreen()`, `activateWindow()`, `raise_()`

#### keyPressEvent(event)
- Se tecla ESC E `allow_skip == True`: emite `skip_requested`
- Caso contrário: propaga evento para superclasse

---

## MultiScreenOverlay

Gerencia overlays em múltiplos monitores. **Não é um QObject** — é uma classe Python simples.

### Estado

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `overlays` | `List[BreakOverlay]` | Lista de overlays criados |

### Métodos

#### create_overlays() → BreakOverlay
- Fecha overlays anteriores via `close_all()`
- Enumera telas via `QApplication.screens()`
- Cria um `BreakOverlay` para cada tela, posicionado na geometria da tela
- **Tela primária (índice 0):** Overlay completo com botões
- **Telas secundárias (índice > 0):** Botões skip e postpone são escondidos (`hide()`)
- Retorna o overlay da tela primária (para conexão de signals)

#### show_all()
Para cada overlay: `showFullScreen()` + `activateWindow()`

#### update_all(seconds_remaining)
Para cada overlay: `update_countdown(seconds_remaining)`

#### close_all()
Para cada overlay: `close()`. Limpa a lista.

#### configure_all(message, duration, allow_skip, allow_postpone, postpone_minutes)
Para cada overlay: `configure(...)` com os mesmos parâmetros.

### Observação sobre Multi-Monitor

Na implementação atual do `WsiBreakTimeApp`, o `MultiScreenOverlay` é instanciado mas **não é utilizado** — o overlay simples (`BreakOverlay`) é usado diretamente com `show_fullscreen()` que se posiciona na tela primária. A infraestrutura multi-monitor está pronta mas não conectada no orquestrador.
