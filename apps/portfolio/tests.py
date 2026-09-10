"""
Testes do portfólio.

Cobrem o que quebraria em silêncio: o contato perdendo mensagem, o filtro
mostrando projeto despublicado, e o comando de semente duplicando registros.
O resto da página é HTML — quebra alto e na cara de quem olha.
"""

import io
from datetime import date
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import (
    Certificado,
    Experiencia,
    FotoVivencia,
    MensagemContato,
    Projeto,
    Tecnologia,
    Vivencia,
)


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
            nome='Python', categoria=Tecnologia.Categoria.STACK
        )
        self.sql = Tecnologia.objects.create(
            nome='SQL', categoria=Tecnologia.Categoria.STACK
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

    def test_habilidades_listam_toda_tecnologia(self):
        """O quadro de habilidades é o currículo, não o índice dos projetos."""
        resposta = self.client.get(reverse('portfolio:home'))
        nomes = [t.nome for t in resposta.context['tecnologias']]
        self.assertIn('SQL', nomes)

    def test_habilidades_saem_na_ordem_do_quadro(self):
        """
        Stack vem ANTES de Ferramentas e de Competências.

        Pela ordenação alfabética do valor gravado a ordem sairia
        "competencias, ferramentas, stack" — a ordem de leitura correta é
        uma decisão de apresentação, não um acaso do banco.
        """
        Tecnologia.objects.create(nome='UML', categoria=Tecnologia.Categoria.COMPETENCIAS)
        Tecnologia.objects.create(nome='Git', categoria=Tecnologia.Categoria.FERRAMENTAS)
        Tecnologia.objects.create(nome='HTML', categoria=Tecnologia.Categoria.STACK)

        resposta = self.client.get(reverse('portfolio:home'))
        categorias = []
        for tec in resposta.context['tecnologias']:
            if tec.categoria not in categorias:
                categorias.append(tec.categoria)

        self.assertEqual(
            categorias,
            ['stack', 'ferramentas', 'competencias'],
        )

    def test_pagina_abre_sem_nenhum_dado(self):
        """Um portfólio recém-clonado não pode devolver 500."""
        Projeto.objects.all().delete()
        Tecnologia.objects.all().delete()
        self.assertEqual(self.client.get(reverse('portfolio:home')).status_code, 200)


class SegundaFaceTests(TestCase):
    """
    A face "fora da área" — as atividades de representação, clubes e MUN.

    O que estes testes protegem é uma decisão de arquitetura que não se lê no
    template: as DUAS faces vêm no mesmo HTML, sempre, e o botão do topo só
    alterna qual está visível. Se alguém um dia trocar isso por carregamento
    sob demanda, a face nova entrará no DOM depois do arranque do
    narrativa.js, sem ScrollTrigger nenhum — e como `html.movimento` deixa
    todo `.revelar` em opacidade 0, ela ficará invisível para sempre. O teste
    que checa as duas faces no mesmo HTML é o que pega essa regressão.
    """

    def setUp(self):
        self.url = reverse('portfolio:home')
        self.vivencia = Vivencia.objects.create(
            titulo='Representante de sala',
            papel='Representante',
            periodo='2025',
            descricao_curta='Ponte entre a turma e a coordenação.',
            publicado=True,
        )

    def test_vivencias_chegam_no_contexto(self):
        resposta = self.client.get(self.url)
        titulos = [v.titulo for v in resposta.context['vivencias']]
        self.assertIn('Representante de sala', titulos)

    def test_vivencia_despublicada_nao_aparece(self):
        Vivencia.objects.create(
            titulo='Rascunho de atividade',
            descricao_curta='Não deve aparecer.',
            publicado=False,
        )
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Representante de sala')
        self.assertNotContains(resposta, 'Rascunho de atividade')

    def test_as_duas_faces_vem_no_mesmo_html(self):
        """
        O ponto central: uma requisição traz as duas faces.

        Não é preferência de estilo — é o que mantém as animações
        funcionando. Ver o docstring da classe.
        """
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'data-face="dev"')
        self.assertContains(resposta, 'data-face="fora"')
        # A face técnica e a de fora, juntas na mesma resposta.
        self.assertContains(resposta, 'id="projetos"')
        self.assertContains(resposta, 'id="vivencias"')

    def test_contato_existe_uma_vez_so(self):
        """
        O formulário de contato serve às duas faces e mora FORA das duas.

        Duplicá-lo criaria ids de campo repetidos (HTML inválido, e cada
        `<label for>` passaria a apontar para o primeiro campo homônimo) e
        dois formulários POST concorrentes na mesma página.
        """
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.content.decode().count('id="contato"'), 1)

    def test_salvar_vivencia_limpa_o_cache(self):
        """Mesma razão dos outros modelos da home — ver os signals."""
        self.client.get(self.url)

        Vivencia.objects.create(
            titulo='Clube de Cinema',
            descricao_curta='Deve aparecer na hora.',
            publicado=True,
        )

        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Clube de Cinema')

    def test_pagina_abre_sem_nenhuma_vivencia(self):
        """A face existe mesmo vazia, com o estado vazio no lugar dos cartões."""
        Vivencia.objects.all().delete()
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'id="vivencias"')

    def test_slug_sai_do_titulo(self):
        self.assertEqual(self.vivencia.slug, 'representante-de-sala')

    def test_galeria_poe_a_principal_na_frente(self):
        """
        A foto do cartão abre primeiro nos detalhes.

        `Vivencia.imagem` e `FotoVivencia` são tabelas diferentes, e a ordem
        entre elas não sai de um ORDER BY — sai desta property. Sem ela, o
        template teria de decidir, e a regra viveria espalhada no HTML.
        """
        self.vivencia.imagem = 'vivencias/principal.png'
        self.vivencia.save()
        FotoVivencia.objects.create(
            vivencia=self.vivencia, imagem='vivencias/b.png', ordem_exibicao=2
        )
        FotoVivencia.objects.create(
            vivencia=self.vivencia, imagem='vivencias/a.png', ordem_exibicao=1
        )

        urls = [url for url, _ in self.vivencia.galeria]
        self.assertEqual(len(urls), 3)
        self.assertIn('principal.png', urls[0])
        # E as extras seguem a ordem de exibição, não a de cadastro.
        self.assertIn('a.png', urls[1])
        self.assertIn('b.png', urls[2])

    def test_galeria_vazia_sem_nenhuma_foto(self):
        """Sem foto nenhuma a galeria não existe, e o modal não a desenha."""
        self.assertEqual(self.vivencia.galeria, [])

    def test_id_do_video_sai_de_qualquer_formato(self):
        """Mesma extração de `Projeto` — a regra é uma só, não duas cópias."""
        for url in [
            'https://www.youtube.com/watch?v=nS2oIIDgPVk',
            'https://youtu.be/nS2oIIDgPVk',
            'https://www.youtube.com/embed/nS2oIIDgPVk',
        ]:
            self.vivencia.link_video = url
            self.assertEqual(self.vivencia.id_video_youtube, 'nS2oIIDgPVk', url)

    def test_sem_video_o_id_e_nulo(self):
        self.vivencia.link_video = ''
        self.assertIsNone(self.vivencia.id_video_youtube)
        self.vivencia.link_video = 'https://exemplo.com/nao-e-youtube'
        self.assertIsNone(self.vivencia.id_video_youtube)

    def test_foto_nova_limpa_o_cache(self):
        """
        Salvar uma foto pelo inline do admin não toca na `Vivencia` dona, então
        o signal dela não cobriria este caso — `FotoVivencia` precisa estar em
        `MODELOS_DA_HOME` por conta própria.

        A checagem é sobre o CONTEXTO e não sobre o HTML: a legenda só é
        desenhada quando a galeria tem mais de uma foto, e amarrar este teste
        a essa condição de layout faria dele um teste de template disfarçado
        de teste de cache — quebraria ao mudar a regra de exibição, sem que o
        cache tivesse nada a ver com isso.
        """
        self.client.get(self.url)

        FotoVivencia.objects.create(
            vivencia=self.vivencia,
            imagem='vivencias/nova.png',
            legenda='Uma legenda qualquer',
        )

        resposta = self.client.get(self.url)
        vivencia = resposta.context['vivencias'][0]
        self.assertEqual(vivencia.fotos.count(), 1)


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

        Foram 6 até o filtro de projetos por tecnologia sair da página — a
        consulta que buscava `tecnologias_em_uso` (as tecnologias com algum
        projeto publicado, para montar os botões do filtro) não existe mais,
        porque o filtro em si não existe mais.

        Antes disso, eram 5 até o cache passar a guardar o CONTEXTO em vez da
        resposta pronta. A diferença naquele momento foi o `prefetch_related`
        das tecnologias: com o queryset preguiçoso, sem nenhum projeto
        cadastrado, o Django pulava a consulta do prefetch; o `list()` passou
        a materializá-la sempre.

        O número aqui não é um N+1 — verificado contando com 3 e com 10
        projetos: mesma contagem nos dois casos, ou seja, não cresce com a
        quantidade de linhas, que é a definição do defeito que este teste
        existe para pegar.

        Subiu de 5 para 6 com a segunda face do site: a consulta das
        `Vivencia`. É uma a mais por VISITA CACHEADA (a cada quinze minutos,
        ou a cada edição no admin), não por acesso — e as duas faces vêm no
        mesmo HTML, então não há requisição nova quando a pessoa troca de
        lado.

        SÃO 6 E NÃO 7 porque este cenário não tem vivência nenhuma
        cadastrada: sem linhas na tabela, o Django pula a consulta do
        `prefetch_related('fotos')` — não há id nenhum para procurar. Com
        atividades cadastradas são 7, e é o `test_galeria_nao_cresce_com_as_
        atividades` logo abaixo que prova que o número para em 7 e não cresce
        com a quantidade delas, que é a definição do N+1 que o prefetch
        existe para evitar.
        """
        with self.assertNumQueries(6):
            self.client.get(self.url)

    def test_galeria_nao_cresce_com_as_atividades(self):
        """
        O prefetch das fotos é uma consulta só, com uma ou com muitas.

        Sem ele, montar a galeria de cada modal custaria uma consulta por
        atividade na tela — o N+1 clássico, que não aparece com um registro de
        teste e explode com o conteúdo real.
        """
        for i in range(6):
            vivencia = Vivencia.objects.create(
                titulo=f'Atividade {i}',
                descricao_curta='.',
                publicado=True,
            )
            FotoVivencia.objects.create(
                vivencia=vivencia, imagem=f'vivencias/{i}.png'
            )

        cache.clear()
        with self.assertNumQueries(7):
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
            Tecnologia.objects.create(nome='Rust', categoria=Tecnologia.Categoria.STACK)
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


class BackendDoResendTests(SimpleTestCase):
    """
    O envio em produção não é SMTP: o plano gratuito do Render bloqueia as
    portas de saída, então o aviso do formulário vai pela API HTTP do Resend.

    Estes testes não tocam a rede — o que se verifica é o CONTRATO com a API:
    o formato do corpo, o cabeçalho de autenticação e o comportamento quando
    algo falha. Um erro aqui só apareceria em produção, no dia em que alguém
    escrevesse pelo formulário.
    """

    def _enviar(self, **kwargs):
        """Envia uma mensagem com a rede mockada e devolve a requisição montada."""
        from django.core.mail import EmailMessage

        with mock.patch('urllib.request.urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b'{"id":"1"}'
            EmailMessage(
                subject='[Portfólio] Assunto',
                body='O corpo da mensagem.',
                to=['destino@exemplo.com'],
                reply_to=['visitante@exemplo.com'],
                **kwargs,
            ).send(fail_silently=False)
            return urlopen.call_args[0][0]

    @override_settings(
        EMAIL_BACKEND='apps.core.email.ResendBackend',
        RESEND_API_KEY='re_chave_de_teste',
        DEFAULT_FROM_EMAIL='Portfólio <onboarding@resend.dev>',
    )
    def test_monta_a_requisicao_no_formato_da_api(self):
        import json

        requisicao = self._enviar()

        self.assertEqual(requisicao.full_url, 'https://api.resend.com/emails')
        self.assertEqual(requisicao.method, 'POST')
        self.assertEqual(
            requisicao.headers.get('Authorization'), 'Bearer re_chave_de_teste'
        )

        corpo = json.loads(requisicao.data.decode('utf-8'))
        self.assertEqual(corpo['to'], ['destino@exemplo.com'])
        self.assertEqual(corpo['subject'], '[Portfólio] Assunto')
        self.assertEqual(corpo['text'], 'O corpo da mensagem.')
        # O `reply_to` é o que faz "Responder" ir para quem escreveu, e não
        # para o remetente técnico. Sem ele o formulário vira uma via de mão
        # única sem ninguém perceber.
        self.assertEqual(corpo['reply_to'], ['visitante@exemplo.com'])

    @override_settings(
        EMAIL_BACKEND='apps.core.email.ResendBackend',
        RESEND_API_KEY='re_chave_de_teste',
        DEFAULT_FROM_EMAIL='Portfolio <onboarding@resend.dev>',
    )
    def test_manda_user_agent_proprio(self):
        """
        Sem User-Agent, o urllib se anuncia como `Python-urllib/3.x` e o
        Cloudflare que protege a API do Resend recusa com "error code: 1010" —
        um 403 sem JSON, que parece erro de chave e nao e.

        Foi o defeito que segurou o envio em producao. O teste existe para o
        cabecalho nao ser removido por parecer decorativo.
        """
        requisicao = self._enviar()

        agente = requisicao.headers.get('User-agent', '')
        self.assertTrue(agente)
        self.assertNotIn('urllib', agente.lower())
        self.assertNotIn('python', agente.lower())

    @override_settings(
        EMAIL_BACKEND='apps.core.email.ResendBackend', RESEND_API_KEY=''
    )
    def test_sem_chave_levanta_em_vez_de_fingir_que_enviou(self):
        """
        Um backend que devolve sucesso sem enviar é pior que um que falha: a
        view marcaria `email_enviado = True` e ninguém saberia que o aviso não
        chegou.
        """
        from django.core.mail import EmailMessage

        with self.assertRaises(ValueError):
            EmailMessage(subject='x', body='y', to=['a@b.com']).send(
                fail_silently=False
            )

    @override_settings(
        EMAIL_BACKEND='apps.core.email.ResendBackend', RESEND_API_KEY='re_x'
    )
    def test_erro_da_api_carrega_o_motivo(self):
        """
        O corpo da resposta é onde o Resend explica o que recusou. Sem ele o
        log ficaria com um código mudo, e a causa exigiria reproduzir a falha.
        """
        import urllib.error

        from django.core.mail import EmailMessage

        falha = urllib.error.HTTPError(
            url='https://api.resend.com/emails',
            code=422,
            msg='Unprocessable',
            hdrs=None,
            fp=io.BytesIO(b'{"message":"domain is not verified"}'),
        )

        with mock.patch('urllib.request.urlopen', side_effect=falha):
            with self.assertRaises(RuntimeError) as contexto:
                EmailMessage(subject='x', body='y', to=['a@b.com']).send(
                    fail_silently=False
                )

        self.assertIn('422', str(contexto.exception))
        self.assertIn('domain is not verified', str(contexto.exception))
