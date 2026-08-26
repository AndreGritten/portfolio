"""
`{% estatico %}` — como o `{% static %}`, mas com a versão do arquivo no fim.

O servidor de desenvolvimento do Django devolve os estáticos com
`Last-Modified` e mais nada: sem `ETag`, sem `Cache-Control`. Sem instrução
explícita, o navegador aplica cache heurístico — ele *pode* reaproveitar o
arquivo que já tem sem sequer perguntar se mudou.

O sintoma é o pior possível de diagnosticar, porque o código no disco está
certo e o que roda está errado. Num projeto cujo CSS é recompilado a cada
ajuste de layout, isso acontece o tempo todo.

`?v=<mtime>` resolve pela raiz: o endereço muda quando o arquivo muda, então o
navegador é obrigado a buscar de novo — e enquanto não muda, pode cachear à
vontade.

Não dá para pôr o cabeçalho no lugar do parâmetro: com o `runserver`, o
`StaticFilesHandler` atende `/static/` antes da fila de middlewares, então um
middleware nunca veria essas respostas.

Uso, no lugar de `{% static %}`, para CSS e JS:

    {% load estaticos %}
    <script defer src="{% estatico 'js/narrativa.js' %}"></script>

Herdado do sistema do CAU/PR.
"""

import pathlib

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def estatico(caminho):
    endereco = static(caminho)

    # Em produção o manifesto do WhiteNoise já põe o hash do conteúdo no nome
    # do arquivo (`app.6db4bb6a48c1.css`), que resolve o mesmo problema de
    # forma melhor. Acrescentar `?v=` ali seria ruído — e ruído com efeito
    # colateral: alguns intermediários se recusam a cachear URL com query.
    #
    # A checagem é do DEBUG, e não "o finder achou o arquivo": com
    # STATICFILES_DIRS configurado o finder encontra a FONTE mesmo depois do
    # collectstatic, então essa pergunta responderia sim nos dois ambientes.
    if not settings.DEBUG:
        return endereco

    absoluto = finders.find(caminho)
    if not absoluto:
        return endereco

    try:
        versao = int(pathlib.Path(absoluto).stat().st_mtime)
    except OSError:
        return endereco

    separador = '&' if '?' in endereco else '?'
    return f'{endereco}{separador}v={versao}'
