# Visão Geral da Arquitetura

## Propósito

**Wsi Break Time** é uma aplicação desktop para Windows que lembra o usuário de fazer pausas regulares para descanso dos olhos. Roda como um processo em segundo plano com ícone na bandeja do sistema (system tray), exibindo overlays fullscreen durante as pausas.

## Versão

- **Versão:** 1.0.0
- **Autor:** Walter Silva
- **Licença:** MIT
- **Linguagem original:** Python 3.9+
- **Framework GUI:** PyQt6 (>= 6.5.0)
- **Empacotamento:** PyInstaller (>= 6.0.0)
- **Plataforma alvo:** Windows 10/11 (com suporte parcial Linux/macOS)

## Características Principais

1. **Pausas programadas** — Intervalos configuráveis com overlay fullscreen
2. **System tray** — Ícone com menu de contexto para controle completo
3. **Multi-monitor** — Overlay exibido em todas as telas conectadas
4. **Notificações** — Pré-avisos e alertas via toast notifications do sistema
5. **TODOs recorrentes** — Tarefas diárias com código de verificação para conclusão
6. **Pomodoro** — Técnica de produtividade com ciclos trabalho/pausa
7. **Lembrete de água** — Notificações periódicas de hidratação
8. **Configurável** — Todas as funcionalidades ajustáveis via dialog de settings

## Idioma da Interface

Toda a interface do usuário está em **português brasileiro** (pt-BR). Isso inclui:
- Menus e labels do system tray
- Textos do overlay de pausa
- Mensagens de notificação
- Dialog de configurações (5 abas: Pausas, Mensagens, Geral, TODOs, Pomodoro)
- Mensagens padrão de pausa

## Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────┐
│                      main.py                                 │
│               (Entry point + QApplication)                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  WsiBreakTimeApp (app.py)                     │
│                   Orquestrador central                       │
│          Conecta todos os componentes via signals            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ TimerManager │  │   TrayIcon   │  │  BreakOverlay +   │  │
│  │              │  │              │  │ MultiScreenOverlay│  │
│  │ timer_       │  │ tray_icon.py │  │                   │  │
│  │ manager.py   │  │              │  │  overlay.py       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────────┘  │
│         │                 │                   │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌───────┴───────────┐  │
│  │ TodoManager  │  │SettingsDialog│  │ PomodoroManager   │  │
│  │              │  │   (app.py)   │  │                   │  │
│  │ todo_        │  │              │  │ pomodoro_          │  │
│  │ manager.py   │  │              │  │ manager.py        │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────┘  │
│         │                 │                                  │
│  ┌──────┴───────┐  ┌──────┴───────┐                         │
│  │  TodoItem    │  │SettingsManager│                         │
│  │  TodoStatus  │  │  AppSettings │                         │
│  │              │  │              │                         │
│  │ todo_model.py│  │ settings.py  │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Arquitetura Event-Driven

A aplicação segue o padrão **Signal/Slot** do Qt. Os componentes são desacoplados e se comunicam exclusivamente via sinais:

- **TimerManager** emite sinais quando é hora da pausa, durante a contagem, etc.
- **TrayIcon** emite sinais quando o usuário interage com o menu
- **BreakOverlay** emite sinais quando o usuário pula ou adia a pausa
- **TodoManager** emite sinais quando TODOs vencem ou são completados
- **PomodoroManager** emite sinais de mudança de estado e ticks

O **WsiBreakTimeApp** (orquestrador) recebe todos os sinais e coordena as ações entre componentes. Nenhum componente referencia outro diretamente — toda comunicação passa pelo orquestrador.

## Persistência

- **Formato:** JSON
- **Caminho:** `%APPDATA%\WsiBreakTime\config.json`
- **Fallback:** `~/WsiBreakTime/config.json` (quando `%APPDATA%` não existe)
- **Criação automática:** O diretório e arquivo são criados na primeira execução
- **Encoding:** UTF-8
- **Tratamento de erros:** Falhas de leitura/escrita são logadas no console; app usa defaults

## Fluxo de Execução Principal

1. `run.py` → adiciona `src/` ao sys.path → importa `main.py`
2. `main.py` → configura High DPI → cria QApplication (sem quit on last window closed)
3. Cria `WsiBreakTimeApp` → instancia todos os componentes → conecta signals → aplica settings
4. `start()` → mostra tray → inicia timers → inicia todo_manager → mostra notificação inicial
5. Event loop do Qt processa eventos indefinidamente
6. `Sair` no menu → para timers → fecha overlay → esconde tray → QApplication.quit()

## Módulos

| Módulo | Arquivo | Tamanho | Responsabilidade |
|--------|---------|---------|-----------------|
| Entry point | `main.py` | 1 KB | Inicialização da QApplication |
| Orquestrador | `app.py` | 40 KB | Integração de componentes, SettingsDialog, TodoVerificationDialog |
| Configurações | `settings.py` | 3 KB | AppSettings (dataclass) + SettingsManager (JSON) |
| Timer | `timer_manager.py` | 6 KB | Intervalos de pausa, countdown, pré-notificação, água |
| Overlay | `overlay.py` | 10 KB | BreakOverlay (fullscreen) + MultiScreenOverlay |
| System Tray | `tray_icon.py` | 11 KB | Ícone, menu, notificações, estados visuais |
| TODO Model | `todo_model.py` | 2 KB | TodoItem (dataclass) + TodoStatus (enum) |
| TODO Manager | `todo_manager.py` | 7 KB | Lifecycle, verificação, reset diário |
| Pomodoro | `pomodoro_manager.py` | 8 KB | State machine de ciclos trabalho/pausa |
| **Total** | | **~88 KB** | |
