"""
Configuração do portfólio de André Gritten.

As convenções seguem o sistema do CAU/PR: `python-decouple` com padrões que
deixam o projeto subir sem nenhum `.env`, WhiteNoise servindo os estáticos e o
mesmo código valendo em desenvolvimento e em produção — o que muda é o valor
das variáveis, nunca o caminho do código.
"""

import os
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

DEBUG = config('DEBUG', default=True, cast=bool)

if not DEBUG and SECRET_KEY == CHAVE_DE_DESENVOLVIMENTO:
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
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}']


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
# ---------------------------------------------------------------------------

if not DEBUG:
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



JAZZMIN_SETTINGS = {
    
}