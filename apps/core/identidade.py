"""
Os dados fixos da página: quem é, onde encontrar, o que o menu lista.

Ficam em código, e não no banco, porque não são conteúdo editável — são a
identidade do site. Um `Projeto` novo entra pelo admin; um número de telefone
muda uma vez a cada vários anos e merece aparecer no diff.

Todos os valores vêm do currículo (`static/docs/curriculo-andre-gritten.pdf`).
"""

PESSOA = {
    'nome': 'André Gritten',
    'nome_completo': 'André Luiz da Silva Gritten',
    'cargo': 'Desenvolvedor de Software Web',
    'formacao': 'Estudante de Engenharia de Software',
    'cidade': 'Curitiba',
    'uf': 'PR',
    # A frase de impacto do topo. Curta de propósito: é a primeira coisa que
    # se lê na página, e Django/PostgreSQL já implicam Python/SQL — nomeá-los
    # de novo seria redundante, não mais completo. "PostgreSQL" é a grafia
    # oficial do produto (P e S maiúsculos, sem espaço) — "Postgre" sozinho
    # não é como o nome se escreve, é só um apelido comum.
    'chamada': 'Desenvolvedor de sistemas web com Django e PostgreSQL.',
    # O perfil da seção "Sobre" — uma LISTA de parágrafos, não um bloco só.
    #
    # "CRUD" e "regras de negócio" saíram: são o básico do trabalho, não uma
    # habilidade que se destaca ao ser nomeada — e apareciam repetidos aqui
    # e na chamada acima. "Modelagem de processos, análise de requisitos"
    # descreve melhor o que de fato diferencia a experiência.
    #
    # Virou dois parágrafos (técnico, depois pessoal) em vez de um só depois
    # que o texto único, mesmo mais longo, ainda deixava um vão vazio embaixo
    # dele: ao lado, na mesma seção, ficam os cards de CAU/PR e PUCPR, mais
    # altos que um bloco de texto compacto. O espaço ENTRE dois parágrafos
    # (a margem que o template aplica) ocupa parte dessa diferença de altura
    # sem esticar artificialmente as linhas — ver o comentário no template
    # sobre por que as estatísticas viraram um bloco à parte por causa desse
    # mesmo tipo de problema.
    'perfil': [
        (
            'Estudante de Engenharia de Software (4º período) na PUCPR, com '
            'experiência profissional em desenvolvimento de software web no '
            'CAU/PR. Atuação com Django e PostgreSQL, além de experiência '
            'acadêmica com Laravel, JavaScript, HTML e CSS. Perfil voltado a '
            'modelagem de processos e análise de requisitos.'
        ),
        (
            'Fora do código, sou comunicativo e criativo na hora de resolver '
            'problema, e tenho facilidade para trabalhar em equipe. Gosto '
            'de organizar e liderar grupos, características que aparecem '
            'tanto nos projetos acadêmicos quanto no dia a dia no CAU/PR, '
            'onde a rotina passa por entender a necessidade de cada setor '
            'antes de transformá-la em sistema.'
        ),
    ],
}

CONTATO = {
    'email': 'dehgritten@gmail.com',
    'telefone': '(41) 99899-0487',
    # Sem espaço nem pontuação, com o código do país: é o formato que o
    # `href="tel:"` exige para o celular discar sem editar o número.
    'telefone_href': '+5541998990487',
    'local': 'Curitiba — PR',
}

# A URL do GitHub existe como constante à parte, e não só dentro de
# REDES_SOCIAIS, porque a seção de projetos também a usa isolada — encaixada
# no meio de uma frase ("acesse o meu GitHub"), não numa lista de ícones de
# rede social. Uma fonte só evita a URL duplicada em dois lugares que podem
# divergir se o usuário do GitHub mudar um dia.
URL_GITHUB = 'https://github.com/AndreGritten'

# `icone` tem de existir em apps/core/icones.json.
REDES_SOCIAIS = [
    {
        'rotulo': 'GitHub',
        'icone': 'Github',
        'href': URL_GITHUB,
    },
    {
        'rotulo': 'LinkedIn',
        'icone': 'Linkedin',
        'href': 'https://www.linkedin.com/in/andr%C3%A9-gritten/',
    },
]

# Âncoras da própria página: o site é uma página só, e o menu salta entre as
# seções. `id` bate com o `id` da <section> correspondente em
# templates/portfolio/home.html — mudar um exige mudar o outro.
ITENS_MENU = [
    {'rotulo': 'Sobre', 'href': '#sobre'},
    {'rotulo': 'Trajetória', 'href': '#trajetoria'},
    {'rotulo': 'Certificações', 'href': '#certificacoes'},
    {'rotulo': 'Projetos', 'href': '#projetos'},
    {'rotulo': 'Habilidades', 'href': '#habilidades'},
    {'rotulo': 'Contato', 'href': '#contato'},
]
