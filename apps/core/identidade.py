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

    # ===================================================================
    # A SEGUNDA FACE — o André fora da área
    #
    # Os textos abaixo alimentam a versão azul do site, que aparece ao
    # clicar em "Conheça o André fora da sua área" no topo.
    #
    # Eles NÃO repetem o `perfil` acima, e isso é deliberado: o segundo
    # parágrafo de lá já AFIRMA "comunicativo, criativo, gosto de liderar
    # grupos". Repetir a afirmação aqui seria dizer duas vezes a mesma
    # coisa; o trabalho desta face é MOSTRAR onde isso aconteceu, e quem
    # mostra são as vivências cadastradas no admin. Por isso o texto daqui
    # apresenta o lado, e as atividades provam.
    # ===================================================================
    'chamada_fora': (
        'Também sou o que acontece entre uma entrega e outra: sala de aula, '
        'centro acadêmico, clube, debate.'
    ),
    'perfil_fora': [
        (
            'Nem tudo que me forma passa por um editor de código. Em boa '
            'parte do que faço na PUCPR o trabalho é o mesmo de sempre — '
            'entender o que um grupo precisa, organizar quem faz o quê e '
            'garantir que a conversa chegue a algum lugar —, só que sem '
            'tela nenhuma no meio.'
        ),
        (
            'É onde eu exercito o que não se aprende em documentação: falar '
            'em público, defender uma ideia sem atropelar a do outro, '
            'sustentar um projeto que depende de gente e não de servidor. '
            'Cada atividade aqui embaixo me ensinou alguma coisa que acabo '
            'usando de volta no trabalho técnico.'
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

# O menu da segunda face. Curto porque a face é curta — três seções contra as
# seis da face técnica.
#
# `#sobre-fora` e não `#sobre`: as DUAS faces existem no mesmo HTML ao mesmo
# tempo (só uma fica visível), e `id` repetido é HTML inválido — o navegador
# rolaria sempre para o primeiro que encontrasse, e a âncora da segunda face
# nunca funcionaria. Ver o comentário do `data-face` em
# templates/portfolio/home.html.
#
# `#contato` é o mesmo das duas faces porque a seção de contato é UMA só,
# fora dos dois wrappers: o formulário tem token CSRF e ids de campo únicos,
# e duplicá-lo criaria ids repetidos e dois POSTs concorrentes.
ITENS_MENU_FORA = [
    {'rotulo': 'Quem sou', 'href': '#sobre-fora'},
    {'rotulo': 'Atividades', 'href': '#vivencias'},
    {'rotulo': 'Contato', 'href': '#contato'},
]
