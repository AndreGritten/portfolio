"""
Três views. O site é uma página só; as outras duas são ações.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from .forms import ContatoForm
from .models import Certificado, Experiencia, Projeto, Tecnologia

logger = logging.getLogger(__name__)

NOME_ARQUIVO_CURRICULO = 'curriculo-andre-gritten.pdf'

# Quinze minutos é o TETO, não o intervalo de atualização: quem edita o admin
# não espera nada, porque os signals limpam o cache na hora (ver signals.py).
# O TTL só cobre o que os signals não alcançam — uma alteração feita direto no
# banco, pelo pgAdmin ou pelo painel do Supabase.
TEMPO_DE_CACHE_DA_HOME = 60 * 15


@cache_page(TEMPO_DE_CACHE_DA_HOME)
def home(request):
    """
    A página inteira.

    CACHEADA, e a razão está na medição: a home faz sete consultas, e contra o
    Supabase em `ca-central-1` cada ida custa ~155ms — `SELECT 1`, a consulta
    mais barata que existe, custa o mesmo. O tempo não está no banco, está na
    distância. Somando, eram ~1,1s de rede para montar uma página que só muda
    quando alguém edita o admin.

    `cache_page` guarda a resposta pronta: a primeira visita paga as consultas,
    as seguintes saem da memória. O TTFB medido em produção era ~950ms.

    O cache é de PROCESSO (LocMemCache), então cada worker do Gunicorn tem o
    seu. Com um worker, como no plano gratuito do Render, isso é indiferente;
    com vários, o pior caso é cada um montar a página uma vez — todos com o
    mesmo conteúdo, porque a página não depende de quem pede.

    Quem edita o admin não espera o TTL: `apps/portfolio/signals.py` limpa o
    cache a cada save/delete dos modelos que aparecem aqui.
    """
    return render(request, 'portfolio/home.html', _contexto_da_home())


@require_POST
def contato(request):
    """
    Recebe o formulário, grava, tenta enviar, redireciona.

    A ORDEM importa: a mensagem é gravada ANTES da tentativa de envio. Se o
    SMTP estiver mal configurado, fora do ar ou lento, o contato já está no
    banco e aparece no admin — o e-mail é a conveniência, não o registro.

    Redireciona em vez de renderizar (PRG) para que recarregar a página não
    reenvie a mensagem.
    """
    form = ContatoForm(request.POST)

    if not form.is_valid():
        # Os erros voltam com o formulário preenchido, e a âncora leva de
        # volta à seção — sem ela o navegador jogaria a pessoa no topo, longe
        # do campo com problema.
        contexto = _contexto_da_home(form)
        return render(request, 'portfolio/home.html', contexto, status=400)

    mensagem = form.save()

    corpo = (
        f'Nome: {mensagem.nome}\n'
        f'E-mail: {mensagem.email}\n'
        f'Assunto: {mensagem.assunto or "(sem assunto)"}\n'
        f'\n{mensagem.mensagem}\n'
    )

    try:
        email = EmailMessage(
            subject=f'[Portfólio] {mensagem.assunto or "Nova mensagem"}',
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_DESTINO],
            # Responder no cliente de e-mail vai direto para quem escreveu.
            # O remetente NÃO pode ser o endereço da pessoa: provedores com
            # SPF/DKIM recusam quem envia em nome de um domínio alheio.
            reply_to=[mensagem.email],
        )
        email.send(fail_silently=False)
    except Exception:
        # Amplo de propósito: SMTPException, socket.timeout, OSError e erro de
        # DNS chegam aqui por caminhos diferentes, e a resposta é a mesma em
        # todos — a mensagem já está salva, então nada se perde.
        logger.exception('Falha ao enviar o e-mail da mensagem %s', mensagem.pk)
        messages.error(
            request,
            'Sua mensagem foi registrada, mas o e-mail de aviso não saiu. '
            'Vou vê-la mesmo assim — se for urgente, me chame pelo LinkedIn.',
        )
    else:
        mensagem.email_enviado = True
        mensagem.save(update_fields=['email_enviado'])
        messages.success(
            request,
            f'Mensagem enviada, {mensagem.nome.split()[0]}. Respondo assim que puder.',
        )

    return HttpResponseRedirect(reverse('portfolio:home') + '#contato')


def curriculo(request):
    """Baixa o PDF do currículo."""
    caminho = settings.BASE_DIR / 'static' / 'docs' / NOME_ARQUIVO_CURRICULO

    if not caminho.exists():
        raise Http404('Currículo não encontrado.')

    return FileResponse(
        caminho.open('rb'),
        as_attachment=True,
        filename=NOME_ARQUIVO_CURRICULO,
        content_type='application/pdf',
    )


def _contexto_da_home(form=None):
    """
    O contexto da home — uma fonte só, para os dois caminhos que a renderizam.

    Antes eram duas cópias: uma na `home` e outra na função de erro do contato.
    O docstring da segunda dizia existir para *evitar* essa duplicação, mas o
    resultado eram as mesmas sete consultas escritas duas vezes, para manter em
    sincronia à mão — e nenhum teste pegaria o dia em que divergissem. Uma
    seção nova entrava num lugar e faltava no outro.

    `form` vem preenchido quando o contato voltou com erro; nos demais casos
    nasce vazio.
    """
    # As tecnologias do FILTRO são só as que algum projeto publicado usa. Uma
    # pílula que não filtra nada é uma promessa que a página não cumpre.
    tecnologias_em_uso = (
        Tecnologia.objects
        .filter(projetos__publicado=True)
        .distinct()
        .order_by('nome')
    )

    return {
        'projetos': (
            Projeto.objects
            .filter(publicado=True)
            .prefetch_related('tecnologias')
        ),
        'tecnologias_filtro': tecnologias_em_uso,
        # Para a seção "Habilidades": todas, agrupadas por categoria no
        # template com `{% regroup %}`. `na_ordem_do_quadro` é o que o regroup
        # exige — ele agrupa vizinhos, então a lista precisa chegar ordenada
        # pela chave do agrupamento, e nesta ordem e não na alfabética.
        # `list()` e não o queryset cru, por causa do `|slice:":6"` que o hero
        # aplica: fatiar um queryset no template não reaproveita o resultado —
        # o Django emite uma SEGUNDA consulta com `LIMIT 6`, e a mesma tabela
        # era lida duas vezes por página. Numa lista já materializada o slice é
        # só Python.
        'tecnologias': list(Tecnologia.objects.na_ordem_do_quadro()),
        'certificados': Certificado.objects.all(),
        'experiencias': Experiencia.objects.filter(
            tipo=Experiencia.Tipo.EXPERIENCIA
        ),
        'formacoes': Experiencia.objects.filter(tipo=Experiencia.Tipo.EDUCACAO),
        # `total_certificados` saiu daqui: era um COUNT numa tabela que a linha
        # acima já traz inteira. O template usa `{{ certificados|length }}`,
        # que conta a lista já carregada — uma ida a menos ao banco.
        'form_contato': form if form is not None else ContatoForm(),
        # O template usa isto para abrir a seção de contato já rolada, com o
        # foco no primeiro campo com erro.
        'contato_com_erro': form is not None,
    }
