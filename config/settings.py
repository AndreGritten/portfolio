"""
Configuração do portfólio de André Gritten.

As convenções seguem o sistema do CAU/PR: `python-decouple` com padrões que
deixam o projeto subir sem nenhum `.env`, WhiteNoise servindo os estáticos e o
mesmo código valendo em desenvolvimento e em produção — o que muda é o valor
das variáveis, nunca o caminho do código.
"""

import os
import sys
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Segurança e ambiente
# ---------------------------------------------------------------------------

# Em desenvolvimento uma chave embutida basta; clonar o repositório e rodar
# continua sendo um passo só. Em produção ela é obrigatória — a checagem logo
# abaixo garante isso, em vez de deixar o site no ar com a chave pública.
CHAVE_DE_DESENVOLVIMENTO = 'django-insecure-portfolio-gritten-nao-use-em-producao'
SECRET_KEY = config('SECRET_KEY', default=CHAVE_DE_DESENVOLVIMENTO)

# O padrão é FALSE, e a inversão é deliberada: o modo perigoso não pode ser o
# que se obtém por omissão.
#
# Com `default=True`, bastava a variável sumir do painel do Render para o site
# subir servindo stack traces — e a página de erro do Django imprime
# `os.environ`, onde moram a senha do Postgres e o api_secret do Cloudinary. A
# guarda da SECRET_KEY logo abaixo não cobre esse caso: ela só roda quando
# DEBUG já é falso.
#
# Quem desenvolve põe DEBUG=True no .env (que o .env.example já documenta).
# É uma linha a mais para o desenvolvedor e uma classe inteira de vazamento a
# menos para produção.
DEBUG = config('DEBUG', default=False, cast=bool)

# A suíte de testes fica de fora da guarda.
#
# Com DEBUG virando `False` por padrão, `manage.py test` num clone limpo
# passou a esbarrar nesta checagem — e a mensagem falava em "subir", que não é
# o que quem roda teste está fazendo. A guarda existe para impedir que o SITE
# seja SERVIDO com a chave pública; rodar teste não serve nada, e exigir uma
# SECRET_KEY para isso só ensina a contorná-la com um valor qualquer.
RODANDO_TESTES = 'test' in sys.argv

if not DEBUG and not RODANDO_TESTES and SECRET_KEY == CHAVE_DE_DESENVOLVIMENTO:
    raise RuntimeError(
        'SECRET_KEY não foi definida e DEBUG está desligado. Gere uma com:\n'
        '    python -c "from django.core.management.utils import '
        'get_random_secret_key as k; print(k())"\n'
        'e configure-a como variável de ambiente antes de subir.'
    )

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,[::1]',
    cast=Csv(),
)

# O Render publica o domínio do serviço nesta variável. Acrescentá-la sozinha
# evita que o primeiro deploy caia em DisallowedHost por uma configuração
# manual esquecida.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF_TRUSTED_ORIGINS derivado de ALLOWED_HOSTS, e não só do hostname do
# Render.
#
# Antes ele existia apenas dentro do `if RENDER_EXTERNAL_HOSTNAME`. Isso
# funciona enquanto o endereço é o `.onrender.com` — e quebra calado no dia em
# que um domínio próprio entrar por ALLOWED_HOSTS: o Django passa a recusar
# todo POST com 403, e o sintoma (o formulário de contato não envia) não
# aponta para a causa.
#
# `localhost` e `127.0.0.1` ficam de fora porque em desenvolvimento o
# CsrfViewMiddleware só exige origem confiável em requisição HTTPS, e o
# runserver fala HTTP. Entradas com porta ou curinga (`*`) também saem: a
# primeira o Django aceitaria, mas o curinga viraria uma origem inválida.
CSRF_TRUSTED_ORIGINS = [
    f'https://{host}'
    for host in ALLOWED_HOSTS
    if host not in ('localhost', '127.0.0.1', '[::1]') and '*' not in host
]


# ---------------------------------------------------------------------------
# Aplicações
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.core',
    'apps.portfolio',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Logo depois do SecurityMiddleware e antes de todo o resto: é a posição
    # que a documentação do WhiteNoise pede para ele atender os estáticos sem
    # pagar o custo dos middlewares seguintes.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.identidade',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

# Duas montagens explícitas, e não um `dj_database_url.config(default=...)`
# com `ssl_require`: aquela forma acrescenta `sslmode` às OPTIONS mesmo quando
# o padrão SQLite é usado, e o SQLite rejeita a opção com um TypeError na
# primeira consulta. Separando os dois casos, cada banco recebe só o que
# entende.
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            # A conexão é reaproveitada por 10 minutos. No plano gratuito do
            # Render, abrir uma conexão nova a cada requisição é uma parte
            # sensível do tempo de resposta.
            conn_max_age=600,
            # Confere se a conexão reaproveitada ainda está viva antes de
            # usá-la; sem isso, uma conexão derrubada pelo servidor vira um
            # erro 500 na primeira requisição depois da ociosidade.
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
                'init_command': (
                    'PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;'
                ),
            },
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Autenticação — só o admin
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Arquivos estáticos
# ---------------------------------------------------------------------------

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ---------------------------------------------------------------------------
# Arquivos de mídia — imagens de projeto e PDFs de certificado
# ---------------------------------------------------------------------------

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# O disco do Render é efêmero: tudo que o admin envia some no deploy seguinte.
# Com CLOUDINARY_URL configurada os arquivos passam a viver no Cloudinary, e o
# mesmo `imagem.url` do template continua valendo — muda o backend, não o
# código.
CLOUDINARY_URL = config('CLOUDINARY_URL', default='')
CLOUDINARY_HABILITADO = bool(CLOUDINARY_URL)

if CLOUDINARY_HABILITADO:
    # O SDK do Cloudinary lê a credencial de os.environ, e o python-decouple
    # NÃO exporta o que encontra no .env. Sem esta linha, quem configura pelo
    # arquivo (e não por variável de ambiente de verdade) vê o storage subir
    # sem credencial nenhuma e falhar só na hora do primeiro upload.
    os.environ.setdefault('CLOUDINARY_URL', CLOUDINARY_URL)

    # `cloudinary_storage` depois do staticfiles: aqui ele serve apenas a
    # mídia. Só quem também entrega os estáticos pelo Cloudinary precisa
    # colocá-lo antes.
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']

STORAGES = {
    'default': {
        'BACKEND': (
            'cloudinary_storage.storage.MediaCloudinaryStorage'
            if CLOUDINARY_HABILITADO
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        # O manifesto põe um hash no nome de cada arquivo, o que permite
        # cache eterno no navegador. Em desenvolvimento ele atrapalha: exige
        # um collectstatic a cada alteração de CSS.
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

# O template `admin/base.html` do django-jazzmin 3.0.5 chama
# `{% static 'vendor/bootswatch' %}` — o CAMINHO DA PASTA do seletor de tema,
# não um arquivo. É um bug do pacote: em modo estrito (o padrão do
# ManifestStaticFilesStorage), qualquer entrada ausente do manifesto derruba
# a página inteira com 500 — e uma pasta nunca tem entrada no manifesto,
# então essa página SEMPRE quebraria em produção.
#
# `WHITENOISE_MANIFEST_STRICT = False` é o mecanismo que o próprio WhiteNoise
# oferece para esse exato cenário: quando o hash não existe, ele devolve a
# URL original sem hash em vez de lançar exceção. O admin continua com cache
# eterno em tudo que tem entrada de verdade; só esse atributo solto do
# Jazzmin passa a apontar para a pasta sem hash, o que não tem efeito visual
# nenhum, porque o JavaScript do Jazzmin só usa esse atributo para montar a
# URL de OUTROS arquivos (que aí sim têm hash) na hora de trocar de tema.
#
# O QUE SE PERDE, e vale saber: isto vale para TODOS os estáticos, não só o do
# Jazzmin. Se um dia o `app.css` sumir do manifesto por um collectstatic
# incompleto, a página passa a renderizar com a URL sem hash e um 404 mudo no
# CSS, em vez de estourar no build. O que segura essa ponta é o `build.sh`,
# que roda `collectstatic --noinput` sob `set -o errexit` — um collectstatic
# quebrado derruba o deploy antes de publicar.
if not DEBUG:
    WHITENOISE_MANIFEST_STRICT = False


# ---------------------------------------------------------------------------
# Mensagens → toasts
# ---------------------------------------------------------------------------

from django.contrib.messages import constants as messages  # noqa: E402

MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'sucesso',
    messages.WARNING: 'aviso',
    messages.ERROR: 'erro',
}


# ---------------------------------------------------------------------------
# E-mail — formulário de contato
# ---------------------------------------------------------------------------

# Em desenvolvimento a mensagem sai no terminal; nenhum SMTP é necessário.
# Em qualquer configuração ela também é gravada em MensagemContato, então uma
# falha de SMTP nunca perde um contato — ver apps/portfolio/views.py.
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = 10  # segundos: um SMTP mudo não pode travar a requisição

DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='Portfólio André Gritten <nao-responda@localhost>',
)

# Para onde vai o que o formulário de contato recebe.
EMAIL_DESTINO = config('EMAIL_DESTINO', default='dedegritten@gmail.com')


# ---------------------------------------------------------------------------
# Endurecimento em produção
#
# Tudo aqui é inerte em desenvolvimento: com DEBUG ligado, redirecionar para
# HTTPS e marcar os cookies como `Secure` quebraria o runserver, que fala HTTP.
#
# E inerte também durante os testes, pelo mesmo motivo: o `Client` de teste
# fala HTTP. Com o redirecionamento ligado ele recebe 301 em vez da página,
# `resposta.context` vem `None`, e onze testes quebram com mensagens que não
# têm nada a ver com a causa ("'NoneType' object is not subscriptable"). Foi
# o que aconteceu quando DEBUG passou a ser `False` por padrão.
#
# Testar HTTPS exigiria um cliente que falasse HTTPS — não é o caso aqui. O
# que se testa é a aplicação; o TLS é do Render.
# ---------------------------------------------------------------------------

if not DEBUG and not RODANDO_TESTES:
    # O Render termina o TLS no proxy e repassa a requisição em HTTP. Sem
    # dizer isso ao Django, `request.is_secure()` é sempre falso e o
    # redirecionamento para HTTPS vira um laço infinito.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Configurável, e não fixo em True, por um motivo prático: é o que permite
    # rodar o modo de produção na máquina local para conferir o manifesto de
    # estáticos e o WhiteNoise. Com o redirecionamento ligado, toda requisição
    # ao 127.0.0.1 vira um 301 para https e não se testa mais nada.
    # Em produção fica ligado — é o padrão.
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Um ano, com subdomínios e pronto para a lista de pré-carga. Só faz
    # sentido depois que o domínio serve HTTPS de forma estável — é o caso do
    # domínio do Render desde o primeiro deploy.
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'



# Identificação do painel. NADA aqui conserta o 500 do admin — quem conserta é
# o WHITENOISE_MANIFEST_STRICT lá em cima, junto de STORAGES. Este bloco é só
# rótulo: nome do site, saudação, rodapé.
JAZZMIN_SETTINGS = {
    'site_title': 'Portfólio',
    'site_header': 'André Gritten',
    'site_brand': 'André Gritten',
    'welcome_sign': 'Painel do portfólio',
    'copyright': 'André Gritten',
    'show_ui_builder': False,
}

# 'darkly' é o tema Bootswatch mais próximo da identidade Ônix & Carmim do
# site público — os dois ficam escuros por padrão, embora as cores de acento
# não sejam as mesmas (o admin usa a paleta padrão do Bootstrap, não o
# carmim). Trocar o acento exigiria um CSS próprio sobre o tema; não vale o
# esforço para uma tela que só André usa.
#
# É escolha estética, não correção: sem esta linha o admin continuaria
# funcionando (com o tema claro padrão), porque o que o mantinha de pé é o
# WHITENOISE_MANIFEST_STRICT.
JAZZMIN_UI_TWEAKS = {
    'theme': 'darkly',
}
