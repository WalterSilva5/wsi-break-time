"""
Script para executar a aplicação durante o desenvolvimento.
Execute com: python run.py
"""

import sys
import os

# Adiciona o diretório src ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'src'))

from main import main

if __name__ == "__main__":
    main()
