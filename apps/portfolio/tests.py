"""
Testes do portfólio.

Cobrem o que quebraria em silêncio: o contato perdendo mensagem, o filtro
mostrando projeto despublicado, e o comando de semente duplicando registros.
O resto da página é HTML — quebra alto e na cara de quem olha.
"""

from datetime import date
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
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

    def test_mensagem_gigante_e_recusada(self):
        """
        Sem teto, `mensagem` é um TextField sem `max_length`: dez megabytes de
        texto eram aceitos, gravados no Postgres (500MB de cota) e colados
        inteiros no corpo do e-mail. Encher banco e caixa de entrada custava
        um `curl`.
        """
        dados = dict(self.dados, mensagem='a' * 20000)
        resposta = self.client.post(self.url, dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(MensagemContato.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_mensagem_no_limite_passa(self):
        """O teto recusa o abuso sem recusar quem escreveu muito de verdade."""
        dados = dict(self.dados, mensagem='a' * 5000)
        resposta = self.client.post(self.url, dados)

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(MensagemContato.objects.count(), 1)

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


CACHE_LOCAL = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'teste-do-cache',
    }
}


@override_settings(CACHES=CACHE_LOCAL)
class CacheDaHomeTests(TestCase):
    """
    O cache existe por um número: sete consultas × ~155ms de latência até o
    Supabase, para uma página que só muda quando alguém edita o admin.

    Em DEBUG o cache é DummyCache, então estes testes forçam o LocMemCache —
    senão passariam sem exercitar nada.
    """

    def setUp(self):
        cache.clear()
        self.url = reverse('portfolio:home')

    def test_segunda_visita_nao_toca_o_banco(self):
        """A primeira paga as consultas; as seguintes saem da memória."""
        self.client.get(self.url)

        with self.assertNumQueries(0):
            resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)

    def test_home_nao_repete_consultas(self):
        """
        Trava o número de consultas para o N+1 não voltar sem ninguém ver.

        Se este teste falhar depois de uma alteração na `home`, a pergunta é se
        a consulta nova é necessária — não se o número deve subir.
        """
        with self.assertNumQueries(5):
            self.client.get(self.url)

    def test_salvar_no_admin_limpa_o_cache(self):
        """
        Sem os signals, editar um projeto e recarregar mostraria a versão velha
        por até quinze minutos — e a pessoa salva de novo, achando que falhou.
        """
        self.client.get(self.url)

        Projeto.objects.create(
            titulo='Projeto recém-criado',
            descricao_curta='Deve aparecer na hora.',
            publicado=True,
        )

        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Projeto recém-criado')

    def test_mudar_tecnologias_limpa_o_cache(self):
        """
        Trocar as tags de um projeto não dispara `post_save` — o Django grava a
        tabela intermediária por fora do `save()`. Sem o receptor de
        `m2m_changed`, a barra de filtros ficaria desatualizada.
        """
        projeto = Projeto.objects.create(
            titulo='Projeto com tags', descricao_curta='.', publicado=True
        )
        self.client.get(self.url)

        projeto.tecnologias.add(
            Tecnologia.objects.create(nome='Rust', categoria=Tecnologia.Categoria.BACKEND)
        )

        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Rust')

    def test_mensagem_de_contato_nao_limpa_o_cache(self):
        """
        `MensagemContato` não aparece na home e é o modelo que mais recebe
        escrita. Invalidar por causa dela jogaria o cache fora a cada contato.
        """
        self.client.get(self.url)

        MensagemContato.objects.create(
            nome='Alguém', email='a@b.com', mensagem='Uma mensagem qualquer.'
        )

        with self.assertNumQueries(0):
            self.client.get(self.url)


class ConfiguracaoTests(SimpleTestCase):
    """
    O settings.py tem duas decisões que só se pagam num cenário que ninguém
    exercita no dia a dia: o dia do deploy mal configurado e o dia do domínio
    próprio. Sem teste, as duas voltam ao estado antigo na primeira refatoração
    e ninguém percebe até doer.
    """

    def _recarregar(self, **ambiente):
        """
        Reimporta o settings com um ambiente controlado.

        `override_settings` não serve aqui: o que se testa é a LÓGICA que
        calcula os valores na importação, não os valores já calculados.
        """
        import importlib
        from unittest import mock

        import config.settings

        with mock.patch.dict('os.environ', ambiente, clear=False):
            return importlib.reload(config.settings)

    def test_debug_e_falso_por_omissao(self):
        """
        Com `default=True`, a variável sumir do painel do Render bastava para o
        site servir stack traces — e a página de erro do Django imprime
        `os.environ`, onde estão a senha do Postgres e o api_secret do
        Cloudinary. O modo perigoso não pode ser o que se obtém por omissão.
        """
        modulo = self._recarregar(DEBUG='')
        self.assertFalse(modulo.DEBUG)

    def test_csrf_cobre_dominio_proprio_sem_o_render(self):
        """
        O CSRF_TRUSTED_ORIGINS vivia dentro do `if RENDER_EXTERNAL_HOSTNAME`.
        No dia em que um domínio próprio entrasse por ALLOWED_HOSTS, todo POST
        passaria a dar 403 — e "o formulário não envia" não aponta para CSRF.
        """
        modulo = self._recarregar(
            ALLOWED_HOSTS='andregritten.com.br,www.andregritten.com.br',
            SECRET_KEY='chave-de-teste',
        )
        self.assertIn('https://andregritten.com.br', modulo.CSRF_TRUSTED_ORIGINS)
        self.assertIn('https://www.andregritten.com.br', modulo.CSRF_TRUSTED_ORIGINS)

    def test_csrf_ignora_localhost(self):
        """
        Em desenvolvimento o runserver fala HTTP, e o CsrfViewMiddleware só
        exige origem confiável em requisição HTTPS. `https://localhost` na
        lista seria ruído que nunca casa.
        """
        modulo = self._recarregar(ALLOWED_HOSTS='localhost,127.0.0.1')
        self.assertEqual(modulo.CSRF_TRUSTED_ORIGINS, [])

    def tearDown(self):
        """Devolve o settings ao estado real, senão os próximos testes herdam o ambiente forjado."""
        import importlib

        import config.settings

        importlib.reload(config.settings)
