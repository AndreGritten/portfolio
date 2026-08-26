"""
Testes do portfólio.

Cobrem o que quebraria em silêncio: o contato perdendo mensagem, o filtro
mostrando projeto despublicado, e o comando de semente duplicando registros.
O resto da página é HTML — quebra alto e na cara de quem olha.
"""

from datetime import date
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Certificado, Experiencia, MensagemContato, Projeto, Tecnologia


class ContatoTests(TestCase):
    """A promessa do formulário: nenhuma mensagem se perde."""

    def setUp(self):
        self.url = reverse('portfolio:contato')
        self.dados = {
            'nome': 'Recrutadora Teste',
            'email': 'recrutadora@exemplo.com',
            'assunto': 'Vaga de estágio',
            'mensagem': 'Vi seu portfólio e gostaria de conversar sobre uma vaga.',
            'site': '',
        }

    def test_envio_valido_grava_e_manda_email(self):
        resposta = self.client.post(self.url, self.dados)

        self.assertRedirects(
            resposta, reverse('portfolio:home') + '#contato',
            fetch_redirect_response=False,
        )

        mensagem = MensagemContato.objects.get()
        self.assertEqual(mensagem.email, 'recrutadora@exemplo.com')
        self.assertTrue(mensagem.email_enviado)
        self.assertFalse(mensagem.lida)

        self.assertEqual(len(mail.outbox), 1)
        # `reply_to` é o que faz "Responder" ir para quem escreveu. O
        # remetente não pode ser o e-mail da pessoa: provedores com SPF/DKIM
        # recusam quem envia em nome de um domínio alheio.
        self.assertEqual(mail.outbox[0].reply_to, ['recrutadora@exemplo.com'])

    def test_falha_de_smtp_nao_perde_a_mensagem(self):
        """
        O teste que justifica o modelo MensagemContato existir.

        Com o SMTP fora do ar a mensagem tem de continuar no banco, marcada
        como não entregue, e a pessoa tem de ver um aviso honesto — não um 500
        nem um "enviado com sucesso" falso.
        """
        with mock.patch(
            'apps.portfolio.views.EmailMessage.send',
            side_effect=OSError('conexão recusada'),
        ):
            resposta = self.client.post(self.url, self.dados, follow=True)

        mensagem = MensagemContato.objects.get()
        self.assertFalse(mensagem.email_enviado)
        self.assertEqual(mensagem.mensagem, self.dados['mensagem'])

        self.assertEqual(resposta.status_code, 200)
        avisos = [str(m) for m in resposta.context['messages']]
        self.assertTrue(any('registrada' in a for a in avisos), avisos)

    def test_honeypot_rejeita_sem_gravar(self):
        dados = dict(self.dados, site='http://spam.exemplo')
        resposta = self.client.post(self.url, dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(MensagemContato.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_mensagem_curta_e_recusada_com_o_campo_marcado(self):
        dados = dict(self.dados, mensagem='oi')
        resposta = self.client.post(self.url, dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(MensagemContato.objects.count(), 0)
        # A borda de 2px é o que separa o campo errado dos outros para quem
        # não distingue o vermelho — e nesta paleta o acento da marca também
        # é vermelho.
        self.assertContains(resposta, 'input-erro', status_code=400)
        self.assertContains(resposta, 'aria-invalid="true"', status_code=400)

    def test_get_nao_e_aceito(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class HomeTests(TestCase):
    def setUp(self):
        self.python = Tecnologia.objects.create(
            nome='Python', categoria=Tecnologia.Categoria.BACKEND
        )
        self.sql = Tecnologia.objects.create(
            nome='SQL', categoria=Tecnologia.Categoria.DATABASE
        )

        self.publicado = Projeto.objects.create(
            titulo='Sistema publicado', descricao_curta='Aparece.', publicado=True
        )
        self.publicado.tecnologias.add(self.python)

        self.escondido = Projeto.objects.create(
            titulo='Rascunho escondido', descricao_curta='Não aparece.', publicado=False
        )
        self.escondido.tecnologias.add(self.sql)

    def test_projeto_despublicado_nao_aparece(self):
        resposta = self.client.get(reverse('portfolio:home'))
        self.assertContains(resposta, 'Sistema publicado')
        self.assertNotContains(resposta, 'Rascunho escondido')

    def test_filtro_so_lista_tecnologia_de_projeto_publicado(self):
        """
        Uma pílula que não filtra nada é uma promessa que a página não cumpre.
        SQL só aparece num projeto despublicado, então não pode virar filtro.
        """
        resposta = self.client.get(reverse('portfolio:home'))
        slugs = [t.slug for t in resposta.context['tecnologias_filtro']]
        self.assertIn('python', slugs)
        self.assertNotIn('sql', slugs)

    def test_habilidades_listam_toda_tecnologia(self):
        """O quadro de habilidades é o currículo, não o índice dos projetos."""
        resposta = self.client.get(reverse('portfolio:home'))
        nomes = [t.nome for t in resposta.context['tecnologias']]
        self.assertIn('SQL', nomes)

    def test_habilidades_saem_na_ordem_do_quadro(self):
        """
        Frontend vem ANTES de Engenharia e de Ferramentas.

        Pela ordenação alfabética do valor gravado ele sairia por último, e o
        `regroup` do template o deixava sozinho numa linha extra. A ordem é
        uma decisão de leitura, não um acaso do banco.
        """
        Tecnologia.objects.create(nome='UML', categoria=Tecnologia.Categoria.ENGENHARIA)
        Tecnologia.objects.create(nome='Git', categoria=Tecnologia.Categoria.FERRAMENTAS)
        Tecnologia.objects.create(nome='HTML', categoria=Tecnologia.Categoria.FRONTEND)

        resposta = self.client.get(reverse('portfolio:home'))
        categorias = []
        for tec in resposta.context['tecnologias']:
            if tec.categoria not in categorias:
                categorias.append(tec.categoria)

        self.assertEqual(
            categorias,
            ['backend', 'database', 'frontend', 'engenharia', 'ferramentas'],
        )

    def test_pagina_abre_sem_nenhum_dado(self):
        """Um portfólio recém-clonado não pode devolver 500."""
        Projeto.objects.all().delete()
        Tecnologia.objects.all().delete()
        self.assertEqual(self.client.get(reverse('portfolio:home')).status_code, 200)


class ModeloTests(TestCase):
    def test_periodo_em_curso(self):
        exp = Experiencia.objects.create(
            tipo=Experiencia.Tipo.EXPERIENCIA,
            cargo='Estagiário de TI',
            organizacao='CAU/PR',
            data_inicio=date(2025, 10, 1),
        )
        self.assertTrue(exp.em_curso)
        self.assertEqual(exp.periodo, '10/2025 — Atual')

    def test_periodo_encerrado(self):
        exp = Experiencia.objects.create(
            tipo=Experiencia.Tipo.EDUCACAO,
            cargo='Engenharia de Software',
            organizacao='PUCPR',
            data_inicio=date(2025, 1, 1),
            data_fim=date(2028, 12, 1),
        )
        self.assertFalse(exp.em_curso)
        self.assertEqual(exp.periodo, '01/2025 — 12/2028')

    def test_atividades_ignoram_linhas_vazias(self):
        exp = Experiencia.objects.create(
            tipo=Experiencia.Tipo.EXPERIENCIA,
            cargo='Cargo', organizacao='Casa',
            data_inicio=date(2025, 1, 1),
            descricao='Primeira.\n\n  Segunda.  \n\n',
        )
        self.assertEqual(exp.atividades, ['Primeira.', 'Segunda.'])

    def test_slug_sai_do_nome(self):
        tec = Tecnologia.objects.create(nome='Engenharia de Requisitos')
        self.assertEqual(tec.slug, 'engenharia-de-requisitos')

    def test_slugs_de_tecnologias_separados_por_espaco(self):
        projeto = Projeto.objects.create(titulo='Projeto', descricao_curta='.')
        projeto.tecnologias.add(
            Tecnologia.objects.create(nome='Python'),
            Tecnologia.objects.create(nome='PostgreSQL'),
        )
        self.assertEqual(
            sorted(projeto.slugs_tecnologias.split()), ['postgresql', 'python']
        )


class SemearTests(TestCase):
    def test_comando_e_idempotente(self):
        """Rodar duas vezes não pode duplicar nada — é o que torna a semente segura."""
        from django.core.management import call_command
        from io import StringIO

        call_command('semear', stdout=StringIO())
        contagens = (
            Tecnologia.objects.count(),
            Certificado.objects.count(),
            Experiencia.objects.count(),
        )
        self.assertGreater(contagens[0], 0)

        call_command('semear', stdout=StringIO())
        self.assertEqual(
            contagens,
            (
                Tecnologia.objects.count(),
                Certificado.objects.count(),
                Experiencia.objects.count(),
            ),
        )


class CurriculoTests(TestCase):
    def test_baixa_como_anexo(self):
        resposta = self.client.get(reverse('portfolio:curriculo'))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'], 'application/pdf')
        self.assertIn('attachment', resposta['Content-Disposition'])
        resposta.close()
