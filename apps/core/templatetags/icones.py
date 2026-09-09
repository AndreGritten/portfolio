"""
Ícones lucide e logos de marca para os templates.

Os desenhos lucide ficam em `apps/core/icones.json`, extraído do pacote
`lucide-static` por `theme/extrair-icones.js`. Os logos de marca (Python,
Django, PostgreSQL...) ficam em `apps/core/icones_marca.json`, extraído
principalmente do pacote `simple-icons` (e, onde falta — hoje só Java —, do
`devicon`) por `theme/extrair-icones-marca.js`. Os dois JSONs são
versionados, então renderizar um ícone não depende de Node nem de rede — só
de acrescentar o nome à lista do script correspondente quando um ícone novo
for usado.

Uso:
    {% load icones %}
    {% icone "Github" size=18 class="text-carmim-claro" %}
    {% icone "ChevronRight" size=15 aria_hidden="true" %}
    {% icone_marca "python" size=16 class="text-carmim-claro" %}
    {% if "python"|tem_icone_marca %}...{% endif %}

A diferença entre as duas tags não é só a fonte: lucide é `stroke`-based
(desenho de linha, `fill="none"`), simple-icons é `fill`-based (silhueta
sólida) — cada catálogo usa o gabarito que combina com o próprio traço.
Ambos herdam `currentColor`, então um logo de marca aparece na paleta do
site (osso, carmim...) em vez das cores oficiais da tecnologia — é
deliberado, ver o comentário em `icone_marca`.

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
CAMINHO_ICONES_MARCA = Path(__file__).resolve().parent.parent / 'icones_marca.json'

# Atributos fixos do <svg>, na ordem em que o lucide os emite.
GABARITO = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}"'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor"'
    ' stroke-width="{espessura}" stroke-linecap="round" stroke-linejoin="round"'
    ' class="{classe}"{extras}>{interno}</svg>'
)

# Simple Icons publica um <path> só, num viewBox 24x24 já normalizado — não
# há stroke-width nem linecap a configurar, é uma silhueta preenchida. Um
# ícone vindo de outra fonte (ex. devicon, para Java) pode ter viewBox
# diferente (128x128), então o gabarito lê o valor do catálogo em vez de
# fixar 24x24 — sem isso, o desenho de outra fonte apareceria cortado.
GABARITO_MARCA = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}"'
    ' viewBox="{viewbox}" fill="currentColor"'
    ' class="{classe}"{extras}><path d="{caminho}"/></svg>'
)


@lru_cache(maxsize=1)
def _catalogo():
    with CAMINHO_ICONES.open(encoding='utf-8') as arquivo:
        return json.load(arquivo)


@lru_cache(maxsize=1)
def _catalogo_marca():
    with CAMINHO_ICONES_MARCA.open(encoding='utf-8') as arquivo:
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


@register.filter
def tem_icone_marca(slug):
    """
    True se `slug` tem logo cadastrado em icones_marca.json.

    Existe para o template decidir, ANTES de tentar desenhar, se reserva o
    espaço do ícone — nem toda tecnologia do quadro tem logo de marca (SQL,
    UML e afins são conceitos, não produtos), e essas tags devem continuar
    só com texto, sem um vazio no lugar do ícone que nunca chega.
    """
    return slug in _catalogo_marca()


@register.simple_tag
def icone_marca(slug, size=24, **kwargs):
    """
    Renderiza o logo de marca de `slug` (ex. "python", "django") pelo path
    do simple-icons — ou nada, em silêncio, se `slug` não tiver logo.

    Ao contrário de `icone` (lucide), aqui a ausência NÃO é erro: o catálogo
    de marca é deliberadamente parcial (ver módulo `theme/extrair-icones-
    marca.js`), e a maioria dos usos deste template passa por `tem_icone_marca`
    antes de chamar esta tag — checar aqui de novo evita alterar essa
    checagem em dois lugares se um dia divergir.

    A cor NUNCA é a oficial da marca: o `fill="currentColor"` do gabarito
    herda a cor do texto ao redor, de propósito — um Python azul-e-amarelo
    ao lado de um Django verde quebraria a paleta do site (osso/carmim), que
    é a identidade que importa aqui, não a identidade de cada tecnologia.
    """
    desenho = _catalogo_marca().get(slug)
    if desenho is None:
        return ''

    classe = f'icone-marca icone-marca-{slug}'
    classe_extra = kwargs.pop('class', '')
    if classe_extra:
        classe = f'{classe} {classe_extra}'

    extras = ''.join(
        f' {chave.replace("_", "-")}="{conditional_escape(valor)}"'
        for chave, valor in kwargs.items()
    )

    return mark_safe(
        GABARITO_MARCA.format(
            tamanho=conditional_escape(size),
            viewbox=conditional_escape(desenho.get('viewBox', '0 0 24 24')),
            classe=conditional_escape(classe),
            extras=extras,
            caminho=conditional_escape(desenho['path']),
        )
    )
