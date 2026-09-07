"""
Envio de e-mail pela API HTTP do Resend.

POR QUE NÃO SMTP: o plano gratuito do Render bloqueia conexões de saída nas
portas 25, 465 e 587. As credenciais do Gmail autenticam e entregam da máquina
local, e a mesma configuração dá timeout em produção — não é problema de
credencial, é a rede. HTTPS não é bloqueado, então uma API resolve.

POR QUE RESEND, e não SendGrid ou Mailgun: os outros exigem um domínio próprio
verificado antes do primeiro envio. O Resend entrega por `onboarding@resend.dev`
sem domínio nenhum, o que importa aqui porque este portfólio não tem domínio.
Se um dia tiver, basta verificá-lo no painel e trocar o DEFAULT_FROM_EMAIL — o
código não muda.

ISTO É UM BACKEND DO DJANGO, e não uma função solta, de propósito: a view
continua chamando `EmailMessage.send()` como sempre. Trocar de provedor, ou
voltar para SMTP, passa a ser uma variável de ambiente em vez de uma alteração
de código. É também o que mantém os testes funcionando com `locmem`.

Sem dependência nova: `urllib` da biblioteca padrão dá conta de um POST com
JSON. Um pacote a mais custaria tempo de build e de arranque frio — que no
plano gratuito já é o gargalo — para economizar poucas linhas.
"""

import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

ENDERECO_API = 'https://api.resend.com/emails'

# O timeout existe pelo mesmo motivo do EMAIL_TIMEOUT do SMTP: uma API muda não
# pode segurar a requisição do visitante. Ele espera uma página, não um e-mail.
TEMPO_LIMITE = 10


class ResendBackend(BaseEmailBackend):
    """Fala com a API do Resend, uma mensagem por requisição."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.chave = getattr(settings, 'RESEND_API_KEY', '')

    def send_messages(self, email_messages):
        """
        Devolve quantas mensagens saíram.

        O contrato do Django pede que o backend engula os erros quando
        `fail_silently` estiver ligado e os propague quando não estiver. A view
        do contato chama com `fail_silently=False` justamente para poder avisar
        o visitante de que o aviso não saiu — e a mensagem dele já está salva
        no banco a essa altura, então nada se perde.
        """
        if not email_messages:
            return 0

        if not self.chave:
            if not self.fail_silently:
                raise ValueError(
                    'RESEND_API_KEY não está definida. Sem ela o backend do '
                    'Resend não tem como autenticar.'
                )
            return 0

        enviadas = 0
        for mensagem in email_messages:
            try:
                self._enviar(mensagem)
            except Exception:
                if not self.fail_silently:
                    raise
            else:
                enviadas += 1
        return enviadas

    def _enviar(self, mensagem):
        corpo = {
            'from': mensagem.from_email or settings.DEFAULT_FROM_EMAIL,
            'to': list(mensagem.to),
            'subject': mensagem.subject,
            'text': mensagem.body,
        }

        # Os opcionais só entram quando existem: a API recusa uma lista vazia
        # em `reply_to`, e `cc`/`bcc` ausentes são diferentes de vazios.
        if mensagem.reply_to:
            corpo['reply_to'] = list(mensagem.reply_to)
        if mensagem.cc:
            corpo['cc'] = list(mensagem.cc)
        if mensagem.bcc:
            corpo['bcc'] = list(mensagem.bcc)

        requisicao = urllib.request.Request(
            ENDERECO_API,
            data=json.dumps(corpo).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {self.chave}',
                'Content-Type': 'application/json',
                # O User-Agent NÃO é enfeite: sem ele o urllib se anuncia como
                # `Python-urllib/3.x`, e o Cloudflare que protege a API do
                # Resend recusa a requisição com "error code: 1010" — uma
                # regra anti-robô que nem chega a olhar a chave.
                #
                # O sintoma engana: vem um 403 sem JSON nenhum, então parece
                # problema de permissão ou de chave inválida. Reproduzido com
                # curl: o MESMO pedido passa com um User-Agent qualquer e é
                # bloqueado com o do Python.
                'User-Agent': 'portfolio-andre-gritten/1.0',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE) as r:
                r.read()
        except urllib.error.HTTPError as erro:
            # O corpo do erro é onde o Resend explica o que recusou — um
            # remetente não verificado, uma chave inválida. Sem ele o log
            # ficaria com um "HTTP 422" mudo, e o próximo leitor teria de
            # reproduzir a falha para descobrir a causa.
            detalhe = erro.read().decode('utf-8', 'replace')[:500]
            raise RuntimeError(
                f'Resend recusou o envio (HTTP {erro.code}): {detalhe}'
            ) from erro
