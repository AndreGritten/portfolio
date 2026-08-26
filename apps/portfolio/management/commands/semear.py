"""
Carrega no banco o conteúdo do currículo.

    python manage.py semear

Existe para que `git clone && migrate && semear && runserver` mostre a página
CHEIA, e não sete seções vazias com "cadastre no admin". Uma página de exemplo
vazia não deixa ninguém julgar o layout — nem quem clona, nem quem a constrói.

É IDEMPOTENTE: roda quantas vezes for preciso sem duplicar nada. Cada registro
é procurado por uma chave natural e atualizado no lugar. O que já foi editado
pelo admin volta ao valor do currículo — é o preço de poder repetir o comando
sem medo, e é o comportamento certo para uma semente.

Os projetos NÃO entram aqui. Inventar um portfólio de projetos seria mentir
sobre o que existe; a seção mostra o estado vazio até André cadastrar os
dele.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.portfolio.models import Certificado, Experiencia, Tecnologia

TECNOLOGIAS = [
    # (nome, categoria, ordem)
    ('Python', Tecnologia.Categoria.BACKEND, 1),
    ('Django', Tecnologia.Categoria.BACKEND, 2),
    ('Laravel', Tecnologia.Categoria.BACKEND, 3),
    ('POO', Tecnologia.Categoria.BACKEND, 4),
    ('Regras de negócio', Tecnologia.Categoria.BACKEND, 5),

    ('PostgreSQL', Tecnologia.Categoria.DATABASE, 1),
    ('SQL', Tecnologia.Categoria.DATABASE, 2),
    ('Modelagem de dados', Tecnologia.Categoria.DATABASE, 3),
    ('ETL', Tecnologia.Categoria.DATABASE, 4),

    ('JavaScript', Tecnologia.Categoria.FRONTEND, 1),
    ('HTML', Tecnologia.Categoria.FRONTEND, 2),
    ('CSS', Tecnologia.Categoria.FRONTEND, 3),

    ('UML', Tecnologia.Categoria.ENGENHARIA, 1),
    ('Engenharia de Requisitos', Tecnologia.Categoria.ENGENHARIA, 2),
    ('CRUD', Tecnologia.Categoria.ENGENHARIA, 3),

    ('Git', Tecnologia.Categoria.FERRAMENTAS, 1),
]

EXPERIENCIAS = [
    {
        'tipo': Experiencia.Tipo.EXPERIENCIA,
        'cargo': 'Estagiário de TI — Desenvolvimento de Software',
        'organizacao': 'Conselho de Arquitetura e Urbanismo do Paraná — CAU/PR',
        'local': 'Curitiba — PR',
        'data_inicio': date(2025, 10, 1),
        'data_fim': None,
        'descricao': (
            'Desenvolvimento e manutenção de sistema web utilizando Python e Django.\n'
            'Desenvolvimento de funcionalidades, CRUDs e regras de negócio.\n'
            'Criação de consultas e rotinas SQL em PostgreSQL para obtenção e '
            'tratamento de dados provenientes de ETL.\n'
            'Correção de bugs e implementação de melhorias no sistema.\n'
            'Participação na análise de requisitos e entendimento dos processos '
            'dos setores.\n'
            'Versionamento de código utilizando Git.'
        ),
        'ordem_exibicao': 1,
    },
    {
        'tipo': Experiencia.Tipo.EDUCACAO,
        'cargo': 'Engenharia de Software',
        'organizacao': 'Pontifícia Universidade Católica do Paraná — PUCPR',
        'local': 'Curitiba — PR',
        'data_inicio': date(2025, 1, 1),
        'data_fim': date(2028, 12, 1),
        'descricao': 'Bacharelado em andamento — 4º período.',
        'ordem_exibicao': 1,
    },
]

CERTIFICADOS = [
    {
        'nome': 'Programação Web com Python e Django Framework',
        'instituicao_emissora': 'Geek University',
        'data_emissao': date(2025, 6, 1),
        'categoria': Certificado.Categoria.WEB,
        'ordem_exibicao': 1,
    },
    {
        'nome': 'Analista de Requisitos',
        'instituicao_emissora': 'PUCPR',
        'data_emissao': date(2025, 11, 1),
        'categoria': Certificado.Categoria.REQUISITOS,
        'ordem_exibicao': 2,
    },
    {
        'nome': 'Desenvolvedor Web',
        'instituicao_emissora': 'PUCPR',
        'data_emissao': date(2025, 11, 1),
        'categoria': Certificado.Categoria.WEB,
        'ordem_exibicao': 3,
    },
    {
        'nome': 'Desenvolvedor de Sistemas Computacionais',
        'instituicao_emissora': 'PUCPR',
        'data_emissao': date(2025, 11, 1),
        'categoria': Certificado.Categoria.PROGRAMACAO,
        'ordem_exibicao': 4,
    },
    {
        'nome': 'Lógica de Programação',
        'instituicao_emissora': 'DIO',
        'data_emissao': date(2025, 3, 1),
        'categoria': Certificado.Categoria.PROGRAMACAO,
        'ordem_exibicao': 5,
    },
]


class Command(BaseCommand):
    help = 'Carrega no banco o conteúdo do currículo (tecnologias, trajetória e certificações).'

    @transaction.atomic
    def handle(self, *args, **opcoes):
        criados = {'tecnologia': 0, 'experiencia': 0, 'certificado': 0}

        for nome, categoria, ordem in TECNOLOGIAS:
            _, novo = Tecnologia.objects.update_or_create(
                slug=slugify(nome),
                defaults={'nome': nome, 'categoria': categoria, 'ordem': ordem},
            )
            criados['tecnologia'] += novo

        for dados in EXPERIENCIAS:
            # Cargo + organização é a chave natural: ninguém ocupa o mesmo
            # cargo duas vezes na mesma casa dentro de um currículo.
            _, novo = Experiencia.objects.update_or_create(
                cargo=dados['cargo'],
                organizacao=dados['organizacao'],
                defaults=dados,
            )
            criados['experiencia'] += novo

        for dados in CERTIFICADOS:
            _, novo = Certificado.objects.update_or_create(
                nome=dados['nome'],
                instituicao_emissora=dados['instituicao_emissora'],
                defaults=dados,
            )
            criados['certificado'] += novo

        self.stdout.write(
            self.style.SUCCESS(
                f'Semeado: {criados["tecnologia"]} tecnologia(s), '
                f'{criados["experiencia"]} entrada(s) de trajetória e '
                f'{criados["certificado"]} certificado(s) criados. '
                f'O que já existia foi atualizado.'
            )
        )
        self.stdout.write(
            'Os projetos NÃO são semeados — cadastre os seus em /admin/portfolio/projeto/.'
        )
