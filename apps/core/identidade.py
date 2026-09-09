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
    # se lê na página, e Django/Postgre já implicam Python/SQL — nomeá-los
    # de novo seria redundante, não mais completo.
    'chamada': 'Desenvolvedor de sistemas web com Django e Postgre.',
    # O parágrafo inteiro do perfil, para a seção "Sobre".
    #
    # "CRUD" e "regras de negócio" saíram: são o básico do trabalho, não uma
    # habilidade que se destaca ao ser nomeada — e apareciam repetidos aqui
    # e na chamada acima. "Modelagem de processos, análise de requisitos"
    # descreve melhor o que de fato diferencia a experiência.
    #
    # Estendido para incluir comunicação, criatividade e liderança/trabalho
    # em equipe — traços reais, não só técnicos, que faltavam aqui. O
    # parágrafo também ficou mais longo de propósito: ao lado, na mesma
    # seção, ficam os cards de CAU/PR e PUCPR, mais altos que o texto
    # original, e a diferença de altura deixava um vão vazio abaixo do
    # parágrafo — ver o comentário no template sobre por que as estatísticas
    # viraram um bloco à parte por causa desse mesmo tipo de problema.
    'perfil': (
        'Estudante de Engenharia de Software (4º período) na PUCPR, com '
        'experiência profissional em desenvolvimento de software web no '
        'CAU/PR. Atuação com Django e Postgre, além de experiência '
        'acadêmica com Laravel, JavaScript, HTML e CSS. Perfil voltado a '
        'modelagem de processos e análise de requisitos, unindo a parte '
        'técnica a um jeito comunicativo e criativo de resolver problema. '
        'Gosto de trabalhar em equipe e tenho facilidade para organizar e '
        'liderar grupos, características que aparecem tanto nos projetos '
        'acadêmicos quanto no dia a dia no CAU/PR, onde a rotina passa por '
        'entender a necessidade de cada setor antes de transformá-la em '
        'sistema.'
    ),
}

CONTATO = {
    'email': 'dehgritten@gmail.com',
    'telefone': '(41) 99899-0487',
    # Sem espaço nem pontuação, com o código do país: é o formato que o
    # `href="tel:"` exige para o celular discar sem editar o número.
    'telefone_href': '+5541998990487',
    'local': 'Curitiba — PR',
}

# `icone` tem de existir em apps/core/icones.json.
REDES_SOCIAIS = [
    {
        'rotulo': 'GitHub',
        'icone': 'Github',
        'href': 'https://github.com/AndreGritten',
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
