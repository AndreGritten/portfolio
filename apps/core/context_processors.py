"""Expõe a identidade do site a todos os templates."""

from .identidade import CONTATO, ITENS_MENU, PESSOA, REDES_SOCIAIS


def identidade(request):
    return {
        'PESSOA': PESSOA,
        'CONTATO': CONTATO,
        'REDES_SOCIAIS': REDES_SOCIAIS,
        'ITENS_MENU': ITENS_MENU,
    }
