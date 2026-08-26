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
from django.views.decorators.http import require_POST

from .forms import ContatoForm
from .models import Certificado, Experiencia, Projeto, Tecnologia

logger = logging.getLogger(__name__)

NOME_ARQUIVO_CURRICULO = 'curriculo-andre-gritten.pdf'


def home(request):
    """A página inteira, numa consulta por seção."""
    projetos = (
        Projeto.objects
        .filter(publicado=True)
        .prefetch_related('tecnologias')
    )

    # As tecnologias do FILTRO são só as que algum projeto publicado usa. Uma
    # pílula que não filtra nada é uma promessa que a página não cumpre.
    tecnologias_em_uso = (
        Tecnologia.objects
        .filter(projetos__publicado=True)
        .distinct()
        .order_by('nome')
    )

    contexto = {
        'projetos': projetos,
        'tecnologias_filtro': tecnologias_em_uso,
        # Para a seção "Habilidades": todas, agrupadas por categoria no
        # template com `{% regroup %}`. `na_ordem_do_quadro` é o que o regroup
        # exige — ele agrupa vizinhos, então a lista precisa chegar ordenada
        # pela chave do agrupamento, e nesta ordem e não na alfabética.
        'tecnologias': Tecnologia.objects.na_ordem_do_quadro(),
        'certificados': Certificado.objects.all(),
        'experiencias': Experiencia.objects.filter(
            tipo=Experiencia.Tipo.EXPERIENCIA
        ),
        'formacoes': Experiencia.objects.filter(tipo=Experiencia.Tipo.EDUCACAO),
        'total_certificados': Certificado.objects.count(),
        'form_contato': ContatoForm(),
    }
    return render(request, 'portfolio/home.html', contexto)


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
        contexto = _contexto_home_com_form(form)
        resposta = render(request, 'portfolio/home.html', contexto, status=400)
        return resposta

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


def _contexto_home_com_form(form):
    """
    Monta o contexto da home reaproveitando o formulário com erros.

    Existe para o caminho de erro do contato não duplicar as consultas que a
    `home` já sabe fazer — e para elas não saírem de sincronia quando uma
    seção nova entrar.
    """
    projetos = Projeto.objects.filter(publicado=True).prefetch_related('tecnologias')
    return {
        'projetos': projetos,
        'tecnologias_filtro': (
            Tecnologia.objects
            .filter(projetos__publicado=True)
            .distinct()
            .order_by('nome')
        ),
        'tecnologias': Tecnologia.objects.na_ordem_do_quadro(),
        'certificados': Certificado.objects.all(),
        'experiencias': Experiencia.objects.filter(tipo=Experiencia.Tipo.EXPERIENCIA),
        'formacoes': Experiencia.objects.filter(tipo=Experiencia.Tipo.EDUCACAO),
        'total_certificados': Certificado.objects.count(),
        'form_contato': form,
        # O template usa isto para abrir a seção de contato já rolada, com o
        # foco no primeiro campo com erro.
        'contato_com_erro': True,
    }
