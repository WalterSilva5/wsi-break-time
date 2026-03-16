# Wsi Break Time — Implementação Python (Legacy)

Este diretório contém a implementação original do Wsi Break Time em Python/PyQt6, preservada para referência durante a migração para Rust.

## Estrutura

```
legacy/python/
├── src/                    # Código fonte Python
│   ├── main.py             # Entry point
│   ├── app.py              # Orquestrador + SettingsDialog
│   ├── settings.py         # Persistência de configurações
│   ├── timer_manager.py    # Gerenciamento de timers
│   ├── overlay.py          # Overlay fullscreen
│   ├── tray_icon.py        # System tray
│   ├── todo_model.py       # Modelo de dados TODO
│   ├── todo_manager.py     # Gerenciamento de TODOs
│   └── pomodoro_manager.py # Técnica Pomodoro
├── build.py                # Script de build cross-platform
├── build.bat               # Build para Windows
├── build.sh                # Build para Linux/macOS
├── build.spec              # Configuração PyInstaller
├── requirements.txt        # Dependências Python
└── run.py                  # Launcher de desenvolvimento
```

## Como executar

```bash
cd legacy/python
pip install -r requirements.txt
python run.py
```

## Documentação detalhada

Consulte `docs/architecture/` na raiz do repositório para documentação completa de cada módulo.

## Status

**Arquivado** — Esta implementação não recebe mais atualizações. A versão ativa está sendo desenvolvida em Rust na raiz do repositório.
