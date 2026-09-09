# syntax=docker/dockerfile:1
#
# Imagem para o Fly.io. Não substitui o Render enquanto os dois rodarem em
# paralelo — este arquivo não é usado no deploy do Render, que continua
# lendo build.sh/Procfile normalmente.
#
# Base python:3.12-slim para casar com o runtime.txt (python-3.12.11), que é
# o que o Render usa hoje. Slim, e não a imagem completa, porque psycopg[binary]
# e Pillow trazem wheels pré-compiladas para as libs de imagem e Postgres mais
# comuns — não é preciso o toolchain de compilação completo da imagem cheia.
FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE evita .pyc no container, que não tem benefício numa
# imagem que roda uma vez e é descartada. PYTHONUNBUFFERED é o que faz os
# logs aparecerem em tempo real em `fly logs` — sem isso o Python armazena a
# saída em buffer e ela só aparece em lotes, e às vezes só quando o processo
# morre. É a mesma razão pela qual o LOGGING do settings.py escreve em stdout.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq5 é a biblioteca cliente do Postgres em runtime. psycopg[binary] traz
# o driver compilado, mas ainda depende dela estar presente no sistema.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# collectstatic roda em BUILD TIME, não em runtime: não depende de nenhum
# segredo de produção (DATABASE_URL, CLOUDINARY_URL), só dos arquivos do
# repositório. Rodar aqui deixa os estáticos já prontos dentro da imagem —
# nenhuma dependência de rede no momento em que o container sobe.
#
# A SECRET_KEY_DE_BUILD abaixo é só para o collectstatic conseguir importar
# settings.py sem esbarrar no guard que recusa SECRET_KEY vazia quando
# DEBUG=False (settings.py, bloco "Segurança e ambiente"). Confirmado por
# teste local: sem NENHUM valor em SECRET_KEY, o collectstatic falha com
# RuntimeError; com qualquer valor, mesmo um dummy, ele passa. Este valor
# nunca é usado em produção — a SECRET_KEY real vem exclusivamente de
# `fly secrets set` e sobrescreve esta em runtime.
ARG SECRET_KEY_DE_BUILD=chave-so-para-o-collectstatic-nao-e-a-de-producao
ENV DJANGO_SETTINGS_MODULE=config.settings \
    SECRET_KEY=$SECRET_KEY_DE_BUILD
RUN python manage.py collectstatic --noinput

# A porta precisa casar com internal_port no fly.toml. Se um mudar, o outro
# precisa mudar junto.
EXPOSE 8080

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8080"]
