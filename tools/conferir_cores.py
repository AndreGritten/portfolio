"""
Confere o contraste da paleta Ônix & Carmim.

    python tools/conferir_cores.py

Sai com código 1 se algum par cair abaixo do piso — é o que impede a regra do
carmim de se perder no primeiro ajuste de tom. A paleta desta página tem uma
particularidade que TORNA esse conferidor necessário e não um luxo:

    O carmim laca (#C2263C) REPROVA como texto: 2,94:1 sobre o fundo dos
    cartões, contra um piso de 4,5:1.

Clarear o vermelho até ele passar sozinho o transformaria em rosa e destruiria
a qualidade fosca que define a marca. A busca numérica mostrou que a janela em
que um tom único serve aos dois papéis existe, mas tem 0,015 de luminância e
encosta em 3,00:1 sem folga nenhuma. Por isso são DOIS tokens com papéis
fixos, e por isso as quatro regras em theme/input.css.

Este arquivo é a conta que sustenta aquelas regras. Mudou um token lá, roda
aqui.

Referência: WCAG 2.1, critérios 1.4.3 (texto, 4,5:1) e 1.4.11 (elementos
gráficos e componentes de interface, 3:1).
"""

import sys

# ---------------------------------------------------------------------------
# A paleta. Tem de bater com theme/input.css.
# ---------------------------------------------------------------------------

ONIX = '#0B0A0C'
BREU = '#141216'
FUNDO = '#1E1B22'

BORDA = '#322D38'
BORDA_FORTE = '#726980'

CARMIM = '#C2263C'
CARMIM_CLARO = '#E5566B'

OSSO = '#F2EDE6'
SECUNDARIA = '#A39BA8'

ERRO = '#FF8080'
AVISO = '#F0B84E'
SUCESSO = '#6FCF97'
INFO = '#8FB4F0'

SUPERFICIES = [('ônix', ONIX), ('breu', BREU), ('cartão', FUNDO)]

PISO_TEXTO = 4.5
PISO_GRAFICO = 3.0


def _linear(canal):
    c = canal / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(hexadecimal):
    h = hexadecimal.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contraste(cor_a, cor_b):
    la, lb = luminancia(cor_a), luminancia(cor_b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


def pares():
    """Todo par que a página realmente usa, com o piso que se aplica a ele."""
    for nome, superficie in SUPERFICIES:
        yield f'osso sobre {nome}', OSSO, superficie, PISO_TEXTO
        yield f'texto secundário sobre {nome}', SECUNDARIA, superficie, PISO_TEXTO
        yield f'carmim claro como texto sobre {nome}', CARMIM_CLARO, superficie, PISO_TEXTO
        yield f'carmim claro como fio/marcador sobre {nome}', CARMIM_CLARO, superficie, PISO_GRAFICO
        yield f'borda forte (contorno de campo) sobre {nome}', BORDA_FORTE, superficie, PISO_GRAFICO

    yield 'osso sobre botão carmim', OSSO, CARMIM, PISO_TEXTO
    yield 'ônix sobre botão osso', ONIX, OSSO, PISO_TEXTO
    yield 'ônix sobre botão carmim claro (hover)', ONIX, CARMIM_CLARO, PISO_TEXTO

    # REGRA 3 — o bloco carmim sólido só pousa em ônix e breu. Sobre o cartão
    # ele dá 2,94:1, e é por isso que `.btn-carmim-em-cartao` existe: 1px de
    # carmim claro devolve a delimitação.
    yield 'bloco carmim sobre ônix', CARMIM, ONIX, PISO_GRAFICO
    yield 'bloco carmim sobre breu', CARMIM, BREU, PISO_GRAFICO
    yield 'contorno do bloco carmim em cartão', CARMIM_CLARO, FUNDO, PISO_GRAFICO

    for nome, cor in [('erro', ERRO), ('aviso', AVISO), ('sucesso', SUCESSO), ('info', INFO)]:
        yield f'estado "{nome}" sobre cartão', cor, FUNDO, PISO_TEXTO


def proibidos():
    """
    Usos que a paleta PROÍBE, e que este conferidor mantém proibidos.

    Se algum dia um destes passar a atingir o piso, a regra correspondente em
    theme/input.css ficou obsoleta e deve sair junto — uma regra que não
    protege mais nada só atrapalha quem lê o código depois.
    """
    yield 'carmim laca como texto sobre cartão (regra 1)', CARMIM, FUNDO, PISO_TEXTO
    yield 'carmim laca como fio sobre cartão (regra 2)', CARMIM, FUNDO, PISO_GRAFICO
    yield 'borda decorativa como contorno de campo (regra 4)', BORDA, FUNDO, PISO_GRAFICO


def main():
    falhas = []

    print('\nPARES EM USO')
    print('-' * 68)
    for nome, frente, fundo, piso in pares():
        razao = contraste(frente, fundo)
        passou = razao >= piso
        selo = 'ok    ' if passou else 'FALHOU'
        print(f'  {razao:6.2f}  (piso {piso})  {selo}  {nome}')
        if not passou:
            falhas.append((nome, razao, piso))

    print('\nUSOS PROIBIDOS — devem continuar reprovando')
    print('-' * 68)
    for nome, frente, fundo, piso in proibidos():
        razao = contraste(frente, fundo)
        ainda_reprova = razao < piso
        selo = 'ok    ' if ainda_reprova else 'MUDOU '
        print(f'  {razao:6.2f}  (piso {piso})  {selo}  {nome}')
        if not ainda_reprova:
            falhas.append((f'{nome} — a regra ficou obsoleta', razao, piso))

    print('-' * 68)
    if falhas:
        print(f'\n{len(falhas)} problema(s):')
        for nome, razao, piso in falhas:
            print(f'  · {nome}: {razao:.2f} contra o piso de {piso}')
        print('\nAjuste theme/input.css ou as regras que dependem desses tons.')
        return 1

    print('\nTodos os pares passam. A paleta está coerente com as quatro regras.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
