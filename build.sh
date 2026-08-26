#!/usr/bin/env bash
# Comando de build do Render.
#
# `set -o errexit` é o que faz um passo quebrado derrubar o deploy em vez de
# publicar um site pela metade: sem ele, um collectstatic que falha ainda
# deixaria o gunicorn subir servindo páginas sem CSS.
set -o errexit

pip install -r requirements.txt

# Antes do migrate: se o banco estiver indisponível o deploy para aqui, com os
# estáticos já prontos, em vez de parar no meio da coleta.
python manage.py collectstatic --noinput
python manage.py migrate
