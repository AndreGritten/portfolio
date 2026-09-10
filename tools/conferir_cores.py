"""
Confere o contraste das paletas do site: Ônix & Carmim e Ônix & Azul.

    python tools/conferir_cores.py

Sai com código 1 se algum par cair abaixo do piso — é o que impede a regra do
acento de se perder no primeiro ajuste de tom. A paleta desta página tem uma
particularidade que TORNA esse conferidor necessário e não um luxo:

    O carmim laca (#C2263C) REPROVA como texto: 2,94:1 sobre o fundo dos
    cartões, contra um piso de 4,5:1.

Clarear o vermelho até ele passar sozinho o transformaria em rosa e destruiria
a qualidade fosca que define a marca. A busca numérica mostrou que a janela em
que um tom único serve aos dois papéis existe, mas tem 0,015 de luminância e
encosta em 3,00:1 sem folga nenhuma. Por isso são DOIS tokens com papéis
fixos, e por isso as quatro regras em theme/input.css.

O MESMO VALE PARA O AZUL, e é a razão de este arquivo conferir as duas: o azul
de preenchimento (#1E5FD8) dá 2,52:1 como texto sobre o cartão. A separação
entre "cor de preenchimento" e "cor que pode ser texto" não é uma peculiaridade
do vermelho — é o que acontece com qualquer acento saturado o bastante para
funcionar como bloco sólido sobre fundo escuro.

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

OSSO = '#F2EDE6'
SECUNDARIA = '#A39BA8'

ERRO = '#FF8080'
AVISO = '#F0B84E'
SUCESSO = '#6FCF97'
INFO = '#8FB4F0'

# Os DOIS acentos, cada um no par (preenchimento, claro). As superfícies e a
# tinta não mudam entre as faces: é a mesma pessoa e o mesmo site, só o acento
# vira. Ver o comentário do `html[data-tema="azul"]` em theme/input.css.
#
# `_claro` é o único dos dois que pode ser texto; o outro é só preenchimento.
# Os nomes das variáveis CSS continuam sendo `--carmim` e `--carmim-claro` nas
# duas faces — leia-os como "o acento" e "o acento legível".
ACENTOS = [
    ('carmim', '#C2263C', '#E5566B'),
    ('azul', '#1E5FD8', '#77A8F7'),
]

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


def pares(acento, acento_claro):
    """
    Todo par que a página realmente usa, com o piso que se aplica a ele.

    `acento` é a cor de preenchimento e `acento_claro` a que pode ser texto —
    os dois papéis que a paleta separa. Recebe-os como argumento em vez de ler
    constantes globais porque as MESMAS conferências valem para as duas faces
    do site (carmim e azul), com os mesmos pisos.
    """
    for nome, superficie in SUPERFICIES:
        yield f'osso sobre {nome}', OSSO, superficie, PISO_TEXTO
        yield f'texto secundário sobre {nome}', SECUNDARIA, superficie, PISO_TEXTO
        yield f'acento claro como texto sobre {nome}', acento_claro, superficie, PISO_TEXTO
        yield f'acento claro como fio/marcador sobre {nome}', acento_claro, superficie, PISO_GRAFICO
        yield f'borda forte (contorno de campo) sobre {nome}', BORDA_FORTE, superficie, PISO_GRAFICO

    yield 'osso sobre botão de acento', OSSO, acento, PISO_TEXTO
    yield 'ônix sobre botão osso', ONIX, OSSO, PISO_TEXTO
    yield 'ônix sobre botão de acento claro (hover)', ONIX, acento_claro, PISO_TEXTO

    # REGRA 3 — o bloco de acento sólido só pousa em ônix e breu. Sobre o
    # cartão ele reprova, e é por isso que `.btn-carmim-em-cartao` existe: 1px
    # de acento claro devolve a delimitação.
    yield 'bloco de acento sobre ônix', acento, ONIX, PISO_GRAFICO
    yield 'bloco de acento sobre breu', acento, BREU, PISO_GRAFICO
    yield 'contorno do bloco de acento em cartão', acento_claro, FUNDO, PISO_GRAFICO

    for nome, cor in [('erro', ERRO), ('aviso', AVISO), ('sucesso', SUCESSO), ('info', INFO)]:
        yield f'estado "{nome}" sobre cartão', cor, FUNDO, PISO_TEXTO


def proibidos(acento):
    """
    Usos que a paleta PROÍBE, e que este conferidor mantém proibidos.

    Se algum dia um destes passar a atingir o piso, a regra correspondente em
    theme/input.css ficou obsoleta e deve sair junto — uma regra que não
    protege mais nada só atrapalha quem lê o código depois.

    A regra 4 (borda decorativa) não depende do acento, então só entra aqui na
    primeira face — repeti-la para cada uma seria barulho no relatório.
    """
    yield 'acento de preenchimento como texto sobre cartão (regra 1)', acento, FUNDO, PISO_TEXTO
    yield 'acento de preenchimento como fio sobre cartão (regra 2)', acento, FUNDO, PISO_GRAFICO


def conferir_acento(rotulo, acento, acento_claro, primeira):
    """Roda as duas baterias para uma face e devolve a lista de falhas."""
    falhas = []

    print(f'\n\n{"=" * 68}')
    print(f'FACE "{rotulo.upper()}"  —  preenchimento {acento} · claro {acento_claro}')
    print('=' * 68)

    print('\nPARES EM USO')
    print('-' * 68)
    for nome, frente, fundo, piso in pares(acento, acento_claro):
        razao = contraste(frente, fundo)
        passou = razao >= piso
        selo = 'ok    ' if passou else 'FALHOU'
        print(f'  {razao:6.2f}  (piso {piso})  {selo}  {nome}')
        if not passou:
            falhas.append((f'[{rotulo}] {nome}', razao, piso))

    print('\nUSOS PROIBIDOS — devem continuar reprovando')
    print('-' * 68)
    proibidos_da_face = list(proibidos(acento))
    if primeira:
        proibidos_da_face.append(
            ('borda decorativa como contorno de campo (regra 4)', BORDA, FUNDO, PISO_GRAFICO)
        )
    for nome, frente, fundo, piso in proibidos_da_face:
        razao = contraste(frente, fundo)
        ainda_reprova = razao < piso
        selo = 'ok    ' if ainda_reprova else 'MUDOU '
        print(f'  {razao:6.2f}  (piso {piso})  {selo}  {nome}')
        if not ainda_reprova:
            falhas.append((f'[{rotulo}] {nome} — a regra ficou obsoleta', razao, piso))

    return falhas


def main():
    falhas = []

    for indice, (rotulo, acento, acento_claro) in enumerate(ACENTOS):
        falhas += conferir_acento(rotulo, acento, acento_claro, primeira=indice == 0)

    print('\n' + '-' * 68)
    if falhas:
        print(f'\n{len(falhas)} problema(s):')
        for nome, razao, piso in falhas:
            print(f'  · {nome}: {razao:.2f} contra o piso de {piso}')
        print('\nAjuste theme/input.css ou as regras que dependem desses tons.')
        return 1

    print(
        f'\nTodos os pares passam, nas {len(ACENTOS)} faces. '
        'As paletas estão coerentes com as quatro regras.'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
