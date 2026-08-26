"""
Ícones lucide para os templates.

Os desenhos ficam em `apps/core/icones.json`, extraído do pacote
`lucide-static` por `theme/extrair-icones.js`. O JSON é versionado, então
renderizar um ícone não depende de Node nem de rede — só de acrescentar o nome
à lista do script quando um ícone novo for usado.

Uso:
    {% load icones %}
    {% icone "Github" size=18 class="text-carmim-claro" %}
    {% icone "ChevronRight" size=15 aria_hidden="true" %}

Herdado do sistema do CAU/PR.
"""

import json
from functools import lru_cache
from pathlib import Path

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

CAMINHO_ICONES = Path(__file__).resolve().parent.parent / 'icones.json'

# Atributos fixos do <svg>, na ordem em que o lucide os emite.
GABARITO = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}"'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor"'
    ' stroke-width="{espessura}" stroke-linecap="round" stroke-linejoin="round"'
    ' class="{classe}"{extras}>{interno}</svg>'
)


@lru_cache(maxsize=1)
def _catalogo():
    with CAMINHO_ICONES.open(encoding='utf-8') as arquivo:
        return json.load(arquivo)


@register.simple_tag
def icone(nome, size=24, **kwargs):
    """Renderiza um ícone lucide pelo nome."""
    desenho = _catalogo().get(nome)

    if desenho is None:
        # Erro alto e cedo, e não um espaço em branco: um ícone que some da
        # página é o tipo de defeito que ninguém nota até alguém reclamar.
        raise template.TemplateSyntaxError(
            f'Ícone "{nome}" não está em apps/core/icones.json. '
            f'Acrescente-o à lista em theme/extrair-icones.js e rode '
            f'`npm run icones`.'
        )

    classe = f'lucide lucide-{desenho["classe"]}'
    classe_extra = kwargs.pop('class', '')
    if classe_extra:
        classe = f'{classe} {classe_extra}'

    espessura = kwargs.pop('stroke_width', 2)

    # Atributos avulsos (aria-hidden, role, focusable...) mantidos como vieram.
    # O sublinhado vira hífen porque `aria-hidden=` não é nome válido de
    # argumento em Python.
    extras = ''.join(
        f' {chave.replace("_", "-")}="{conditional_escape(valor)}"'
        for chave, valor in kwargs.items()
    )

    return mark_safe(
        GABARITO.format(
            tamanho=conditional_escape(size),
            espessura=conditional_escape(espessura),
            classe=conditional_escape(classe),
            extras=extras,
            interno=desenho['interno'],
        )
    )
