"""Formulário de contato."""

from django import forms

from .models import MensagemContato


class ContatoForm(forms.ModelForm):
    """
    O formulário da última seção da página.

    O campo `site` é um honeypot: fica escondido do olho e do leitor de tela,
    e uma pessoa nunca o preenche. Robô de spam preenche todo campo que
    encontra, então qualquer valor ali reprova o envio.

    Honeypot e não CAPTCHA: um CAPTCHA é atrito real para quem quer falar com
    você, e a quantidade de spam que uma página pessoal recebe não justifica
    cobrar esse pedágio de todo mundo.
    """

    site = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true',
        }),
    )

    class Meta:
        model = MensagemContato
        fields = ('nome', 'email', 'assunto', 'mensagem')
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'input-base',
                'placeholder': 'Como devo te chamar',
                'autocomplete': 'name',
                'maxlength': '120',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-base',
                'placeholder': 'seu@email.com',
                'autocomplete': 'email',
            }),
            'assunto': forms.TextInput(attrs={
                'class': 'input-base',
                'placeholder': 'Sobre o que quer falar',
                'maxlength': '160',
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'input-base',
                'rows': 5,
                'placeholder': 'Escreva aqui.',
            }),
        }
        labels = {
            'nome': 'Nome',
            'email': 'E-mail',
            'assunto': 'Assunto',
            'mensagem': 'Mensagem',
        }
        error_messages = {
            'nome': {'required': 'Diga seu nome, por favor.'},
            'email': {
                'required': 'Preciso do seu e-mail para responder.',
                'invalid': 'Esse e-mail parece incompleto — confira o @ e o domínio.',
            },
            'mensagem': {'required': 'Escreva sua mensagem antes de enviar.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            return

        # O Django não marca o widget de um campo com erro — `error_css_class`
        # só alcança a linha inteira nos renderizadores automáticos, e aqui
        # cada campo é escrito à mão no template.
        #
        # `.input-erro` engrossa a borda para 2px. Isso importa mais nesta
        # paleta do que na média: o vermelho de erro e o carmim da marca são o
        # mesmo matiz, então quem não os distingue precisa da ESPESSURA para
        # achar o campo errado.
        #
        # `aria-invalid` e `aria-describedby` dizem a mesma coisa a quem usa
        # leitor de tela. O id casa com o do partials/erros_campo.html.
        for nome, campo in self.fields.items():
            if not self.errors.get(nome):
                continue

            classes = campo.widget.attrs.get('class', '')
            campo.widget.attrs['class'] = f'{classes} input-erro'.strip()
            campo.widget.attrs['aria-invalid'] = 'true'
            campo.widget.attrs['aria-describedby'] = f'erro-id_{nome}'

    def clean_site(self):
        if self.cleaned_data.get('site'):
            # Mensagem genérica de propósito: dizer "você caiu no honeypot"
            # ensinaria o robô a evitá-lo da próxima vez.
            raise forms.ValidationError('Não foi possível enviar. Tente novamente.')
        return ''

    # Teto do que cabe numa mensagem de contato. Cinco mil caracteres são umas
    # duas páginas — folgado para uma proposta de trabalho, e é o ponto.
    #
    # Sem teto, `mensagem` é um TextField sem `max_length`: um POST de dez
    # megabytes era aceito, gravado no Postgres (500MB de cota) e ainda COLADO
    # INTEIRO no corpo do e-mail que a view dispara. Encher o banco e a caixa
    # de entrada de uma vez custava um `curl`.
    TAMANHO_MAXIMO_MENSAGEM = 5000

    def clean_mensagem(self):
        mensagem = self.cleaned_data['mensagem'].strip()

        if len(mensagem) < 10:
            raise forms.ValidationError(
                'A mensagem está curta demais — escreva pelo menos uma frase.'
            )

        if len(mensagem) > self.TAMANHO_MAXIMO_MENSAGEM:
            # A mensagem diz o limite e o excesso: sem os dois números, quem
            # escreveu de verdade um texto longo não sabe quanto cortar.
            raise forms.ValidationError(
                f'A mensagem passou de {self.TAMANHO_MAXIMO_MENSAGEM:,} caracteres '
                f'(são {len(mensagem):,}). Resuma ou mande o resto por e-mail.'
                .replace(',', '.')
            )

        return mensagem
