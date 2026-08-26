"""
Gera static/img/og-image.png — a prévia que aparece quando o link é
compartilhado.

    python tools/gerar_og.py

O PNG é versionado; este script só precisa rodar de novo se o nome, o cargo ou
a paleta mudarem.

POR QUE UM SCRIPT, e não uma imagem feita à mão: a prévia repete o topo do
site, e uma cópia manual envelhece calada — o site muda de acento e o card
continua com o antigo por meses, sem ninguém notar, porque ninguém vê a
própria prévia. Aqui as cores vêm das mesmas constantes que
tools/conferir_cores.py mede.

As fontes são baixadas em TTF para uma pasta temporária, porque o Pillow não
lê woff2 — os woff2 de static/fonts/ servem ao navegador, e nada mais. Nenhum
TTF entra no repositório.
"""

import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('Pillow não está instalado. Rode: pip install -r requirements.txt')

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / 'static' / 'img' / 'og-image.png'

L, A = 1200, 630

# Os mesmos valores de theme/input.css.
ONIX = (11, 10, 12)
BREU = (20, 18, 22)
FUNDO = (30, 27, 34)
CARMIM = (194, 38, 60)
CARMIM_CLARO = (229, 86, 107)
OSSO = (242, 237, 230)
SECUNDARIA = (163, 155, 168)

# SEM User-Agent, e isso é a decisão que faz o script funcionar.
#
# O Google Fonts serve o formato que ele acha que o cliente entende, e o
# Pillow só lê TTF. Medindo os três casos:
#
#   sem cabeçalho (urllib)            -> format('truetype'), magic 00 01 00 00
#   User-Agent de navegador moderno   -> woff2
#   User-Agent de navegador antigo    -> EOT (magic EC 42 01 00), que o Pillow
#                                        recusa com "unknown file format"
#
# O caminho intuitivo — "finjo ser um navegador velho para receber o formato
# velho" — é justamente o errado. O cliente desconhecido recebe TTF.
#
# As URLs devolvidas NÃO terminam em `.ttf` (são do tipo `/l/font?kit=...`):
# o que chega é TTF pelo conteúdo, não pelo nome.

# Um peso fixo por papel, e não a faixa variável. Pedir `wght@800` devolve uma
# INSTÂNCIA ESTÁTICA já no peso certo — o que evita depender de o FreeType
# desta máquina saber aplicar eixos variáveis, que é justamente a parte que
# falha em silêncio e devolveria um card com o nome em peso normal.
PESOS = {
    'nome': ('Bricolage+Grotesque:wght@800', 96),
    'cargo': ('Instrument+Sans:wght@600', 30),
    'lead': ('Instrument+Sans:wght@400', 24),
    'mono': ('JetBrains+Mono:wght@500', 20),
    'marca': ('JetBrains+Mono:wght@700', 26),
}


def baixar_ttf(consulta, pasta):
    url = f'https://fonts.googleapis.com/css2?family={consulta}&display=swap'
    with urllib.request.urlopen(url, timeout=30) as resposta:
        css = resposta.read().decode('utf-8')

    fontes = re.findall(r'url\((https://[^)]+)\)', css)
    if not fontes:
        raise RuntimeError(f'Nenhuma fonte no CSS de {consulta}')

    with urllib.request.urlopen(fontes[0], timeout=30) as resposta:
        dados = resposta.read()

    # Confere o formato em vez de confiar: um TTF começa com 00 01 00 00 ou
    # com "true". Sem esta guarda, um formato inesperado só apareceria lá na
    # frente como "unknown file format" do Pillow, sem dizer o que chegou.
    if dados[:4] not in (b'\x00\x01\x00\x00', b'true'):
        raise RuntimeError(
            f'O Google devolveu algo que não é TTF para {consulta}: '
            f'começa com {dados[:4]!r}.'
        )

    destino = pasta / (re.sub(r'[^A-Za-z0-9]', '', consulta)[:32] + '.ttf')
    destino.write_bytes(dados)
    return destino


def carregar(pasta, papel):
    consulta, tamanho = PESOS[papel]
    return ImageFont.truetype(str(baixar_ttf(consulta, pasta)), tamanho)


def principal():
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)

        f_nome = carregar(pasta, 'nome')
        f_cargo = carregar(pasta, 'cargo')
        f_lead = carregar(pasta, 'lead')
        f_mono = carregar(pasta, 'mono')
        f_marca = carregar(pasta, 'marca')

        imagem = Image.new('RGB', (L, A), ONIX)
        pincel = ImageDraw.Draw(imagem)

        # Gradiente diagonal do fundo até o ônix, linha a linha.
        for y in range(A):
            t = y / A
            cor = tuple(
                round(FUNDO[i] + (ONIX[i] - FUNDO[i]) * min(1, t * 1.5))
                for i in range(3)
            )
            pincel.line([(0, y), (L, y)], fill=cor)

        # A malha técnica, a 5,5% como no CSS.
        malha = tuple(round(c + (OSSO[c_i] - c) * 0.055) for c_i, c in enumerate(BREU))
        for x in range(0, L, 56):
            pincel.line([(x, 0), (x, A)], fill=malha)
        for y in range(0, A, 56):
            pincel.line([(0, y), (L, y)], fill=malha)

        m = 80  # margem

        # Monograma: quadrado vazado com contorno de carmim claro (regra 2 —
        # aqui a cor é sinal, então é o claro e não o laca).
        pincel.rounded_rectangle([m, m, m + 76, m + 76], radius=18,
                                 outline=CARMIM_CLARO, width=3)
        caixa = pincel.textbbox((0, 0), 'AG', font=f_marca)
        pincel.text(
            (m + 38 - (caixa[2] - caixa[0]) / 2, m + 38 - (caixa[3] - caixa[1]) / 2 - caixa[1]),
            'AG', font=f_marca, fill=CARMIM_CLARO,
        )

        pincel.text((m + 100, m + 26), 'CURITIBA · PR', font=f_mono, fill=CARMIM_CLARO)

        # O nome, em CAIXA-ALTA.
        y = 232
        pincel.text((m, y), 'ANDRÉ GRITTEN', font=f_nome, fill=OSSO)

        # O fio de acento.
        y += 116
        pincel.rounded_rectangle([m, y, m + 96, y + 5], radius=2, fill=CARMIM_CLARO)

        y += 38
        pincel.text((m, y), 'Desenvolvedor de Software Web', font=f_cargo, fill=OSSO)

        y += 46
        pincel.text(
            (m, y),
            'Estudante de Engenharia de Software na PUCPR.',
            font=f_lead, fill=SECUNDARIA,
        )

        # As tags, no rodapé. O laca PREENCHE (regra 1) e o osso escreve em
        # cima: 4,96:1.
        y = A - 108
        x = m
        for i, texto in enumerate(['PYTHON', 'DJANGO', 'POSTGRESQL', 'SQL', 'GIT']):
            caixa = pincel.textbbox((0, 0), texto, font=f_mono)
            largura = caixa[2] - caixa[0] + 30
            destaque = i < 2
            pincel.rounded_rectangle(
                [x, y, x + largura, y + 42],
                radius=9,
                fill=CARMIM if destaque else None,
                outline=None if destaque else (50, 45, 56),
                width=1,
            )
            pincel.text(
                (x + 15, y + 21 - (caixa[3] + caixa[1]) / 2),
                texto, font=f_mono, fill=OSSO if destaque else SECUNDARIA,
            )
            x += largura + 12

        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        imagem.save(DESTINO, 'PNG', optimize=True)

        tamanho_kb = os.path.getsize(DESTINO) / 1024
        print(f'Gerado {DESTINO.relative_to(RAIZ)} ({L}×{A}, {tamanho_kb:.0f} KB)')


if __name__ == '__main__':
    principal()
