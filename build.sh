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

# Superusuário na primeira subida.
#
# O `createsuperuser --noinput` lê nativamente DJANGO_SUPERUSER_USERNAME,
# _EMAIL e _PASSWORD. Sem as três variáveis o bloco inteiro é pulado, então
# este passo é inócuo em qualquer deploy que não precise dele.
#
# O `|| true` é obrigatório sob `set -o errexit`: a partir do segundo deploy o
# usuário já existe, o comando sai com erro e derrubaria o build inteiro por
# uma condição que é a esperada.
#
# DEPOIS DO PRIMEIRO DEPLOY, remova DJANGO_SUPERUSER_PASSWORD do painel do
# Render. Senha de admin em texto plano na configuração do serviço é um
# problema pior do que o que ela resolveu.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] \
  && [ -n "$DJANGO_SUPERUSER_EMAIL" ] \
  && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || true
fi
