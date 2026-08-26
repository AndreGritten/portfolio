#!/usr/bin/env python
"""Utilitário de linha de comando do Django."""

import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Não foi possível importar o Django. Ele está instalado e o '
            'ambiente virtual está ativo? Se não, rode:\n'
            '    python -m venv .venv\n'
            '    .venv\\Scripts\\activate        (Windows)\n'
            '    source .venv/bin/activate      (Linux/macOS)\n'
            '    pip install -r requirements.txt'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
