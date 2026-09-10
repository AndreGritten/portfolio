"""Expõe a identidade do site a todos os templates."""

from .identidade import (
    CONTATO,
    ITENS_MENU,
    ITENS_MENU_FORA,
    PESSOA,
    REDES_SOCIAIS,
    URL_GITHUB,
)


def identidade(request):
    return {
        'PESSOA': PESSOA,
        'CONTATO': CONTATO,
        'REDES_SOCIAIS': REDES_SOCIAIS,
        'ITENS_MENU': ITENS_MENU,
        'ITENS_MENU_FORA': ITENS_MENU_FORA,
        'URL_GITHUB': URL_GITHUB,
    }
