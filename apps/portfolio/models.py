"""
Os dados que o admin edita.

Cinco modelos, e dois deles merecem justificativa por não estarem no pedido
original:

`Tecnologia` existe como modelo — e não como texto solto num campo — porque a
mesma lista alimenta DUAS seções: o filtro dos projetos e o quadro de
habilidades. Como texto, elas se desencontrariam no primeiro projeto novo
cadastrado com "PostgresSQL" em vez de "PostgreSQL".

`Experiencia` existe para a linha do tempo ser editável. Escrita no template,
cada emprego novo viraria um commit.
"""

import re

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Case, IntegerField, Value, When
from django.utils.text import slugify

# Casa os três formatos de URL que alguém colaria a partir da barra de
# endereço ou do botão "Compartilhar" do YouTube:
#   watch?v=ID        — a página normal do vídeo
#   youtu.be/ID       — o link curto que o botão "Compartilhar" gera
#   embed/ID          — caso alguém cole o link que já é de incorporação
# O ID do YouTube é sempre 11 caracteres em [A-Za-z0-9_-], então travar o
# tamanho evita capturar parâmetros extras que venham colados depois (como
# `&t=30s` de um link com timestamp).
PADRAO_ID_YOUTUBE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)


def storage_de_arquivo():
    """
    Onde os PDFs de certificado são guardados.

    Callable, e não uma instância: o Django avalia isto na hora do acesso, o
    que mantém a migração igual nos dois ambientes — quem gera a migração sem
    Cloudinary configurado não grava o backend errado dentro dela.

    `RawMediaCloudinaryStorage` e não o de mídia comum: o Cloudinary trata PDF
    como recurso do tipo "image" por padrão, e entregá-lo assim exige liberar
    a entrega de PDF na conta. Como "raw" o arquivo sai como veio.
    """
    if getattr(settings, 'CLOUDINARY_HABILITADO', False):
        from cloudinary_storage.storage import RawMediaCloudinaryStorage

        return RawMediaCloudinaryStorage()
    return default_storage


class TecnologiaQuerySet(models.QuerySet):
    def na_ordem_do_quadro(self):
        """
        Ordena pelas categorias na ordem em que a seção de habilidades as lê.

        Existe porque o `ordering` do modelo classifica pelo VALOR gravado, e
        esse valor é alfabético: competencias, ferramentas, stack — fora da
        sequência que a pessoa espera (o que roda de fato, o que cerca o
        trabalho, o raciocínio por trás).

        Um `Case` resolve sem tocar no que está gravado. A alternativa seria
        renomear os valores para 'a-stack', 'b-ferramentas'… — uma migração e
        um dado feio para sempre, só para agradar a um ORDER BY.
        """
        pesos = [
            When(categoria=valor, then=Value(indice))
            for indice, valor in enumerate(self.model.ORDEM_DO_QUADRO)
        ]
        return self.alias(
            peso=Case(*pesos, default=Value(99), output_field=IntegerField()),
        ).order_by('peso', 'ordem', 'nome')


class Tecnologia(models.Model):
    """Uma tag técnica. Alimenta o filtro de projetos e o quadro de habilidades."""

    class Categoria(models.TextChoices):
        # O que roda de fato: linguagens, frameworks, bancos de dados — a
        # pilha que compõe o sistema em produção.
        STACK = 'stack', 'Stack'
        # O que cerca o trabalho com a stack sem ser a stack em si: editor,
        # controle de versão, containerização.
        FERRAMENTAS = 'ferramentas', 'Ferramentas'
        # Paradigma, técnica, processo, método — o raciocínio por trás do
        # código, não uma tecnologia que se instala. "Competências" e não
        # "Habilidades" para não repetir o nome da seção inteira
        # (`id="habilidades"` no template).
        COMPETENCIAS = 'competencias', 'Competências'

    # A ordem das colunas na seção de habilidades. Uma categoria nova que não
    # entre nesta lista cai no fim, o que é o comportamento certo: aparece,
    # sem se meter no meio de uma sequência pensada.
    ORDEM_DO_QUADRO = [
        Categoria.STACK,
        Categoria.FERRAMENTAS,
        Categoria.COMPETENCIAS,
    ]

    objects = TecnologiaQuerySet.as_manager()

    nome = models.CharField('nome', max_length=60, unique=True)
    slug = models.SlugField(
        'identificador',
        max_length=60,
        unique=True,
        blank=True,
        help_text='Gerado a partir do nome. É o que o filtro de projetos usa '
                  'no HTML — mudar depois de publicado quebra links salvos.',
    )
    categoria = models.CharField(
        'categoria',
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.STACK,
        help_text='Define em qual coluna da seção "Habilidades" a tag aparece.',
    )
    ordem = models.PositiveIntegerField(
        'ordem',
        default=0,
        help_text='Menor primeiro, dentro da categoria.',
    )

    class Meta:
        verbose_name = 'tecnologia'
        verbose_name_plural = 'tecnologias'
        ordering = ['categoria', 'ordem', 'nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Projeto(models.Model):
    titulo = models.CharField('título', max_length=120)
    slug = models.SlugField('identificador', max_length=140, unique=True, blank=True)
    descricao_curta = models.CharField(
        'descrição curta',
        max_length=200,
        help_text='Uma ou duas linhas. É o que aparece no cartão — o limite de '
                  '200 caracteres existe para os cartões da grade ficarem da '
                  'mesma altura.',
    )
    descricao = models.TextField(
        'descrição completa',
        blank=True,
        help_text='Opcional. Aparece ao abrir o projeto.',
    )
    imagem = models.ImageField(
        'imagem',
        upload_to='projetos/',
        blank=True,
        help_text='Proporção 16:9 fica melhor no cartão. Sem imagem, o cartão '
                  'mostra a malha técnica no lugar.',
    )
    tecnologias = models.ManyToManyField(
        Tecnologia,
        verbose_name='tecnologias',
        blank=True,
        related_name='projetos',
    )
    link_github = models.URLField('link do GitHub', blank=True)
    link_deploy = models.URLField('link do site publicado', blank=True)
    link_video = models.URLField(
        'link do vídeo (YouTube)',
        blank=True,
        help_text='Cole a URL da página do vídeo no YouTube, do jeito que '
                  'aparece na barra de endereço — funciona com o link '
                  'completo, o link curto (youtu.be) ou o link de '
                  '"compartilhar". Recomendado como "não listado" para não '
                  'aparecer em busca nem no seu canal, só para quem tem o '
                  'link. Abre num player embutido, sem sair do site.',
    )

    destaque = models.BooleanField(
        'em destaque',
        default=False,
        help_text='Projetos em destaque aparecem primeiro, antes da ordem de '
                  'exibição.',
    )
    publicado = models.BooleanField(
        'publicado',
        default=True,
        help_text='Desmarque para esconder do site sem apagar o cadastro.',
    )
    ordem_exibicao = models.PositiveIntegerField('ordem de exibição', default=0)

    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'projeto'
        verbose_name_plural = 'projetos'
        # Destaque primeiro (`-destaque` põe True na frente), depois a ordem
        # manual, e o mais recente desempata.
        ordering = ['-destaque', 'ordem_exibicao', '-criado_em']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    @property
    def id_video_youtube(self):
        """
        O ID de 11 caracteres do vídeo, extraído de qualquer formato de URL
        que alguém cole no admin — ou `None` sem vídeo ou com um link que não
        bate com nenhum formato reconhecido do YouTube.

        Fica aqui, e não no template, porque a extração é uma regra de
        negócio (o que conta como "link válido do YouTube"), não uma
        formatação de exibição — e uma regex não pertence a um template
        Django, que não tem como testá-la isoladamente.
        """
        if not self.link_video:
            return None
        casado = PADRAO_ID_YOUTUBE.search(self.link_video)
        return casado.group(1) if casado else None


class Vivencia(models.Model):
    """
    Uma atividade fora do desenvolvimento — o lado que o quadro técnico não
    mostra: representante de sala, Centro Acadêmico, clubes, MUN.

    Existe como modelo separado de `Projeto`, e não como um campo "tipo" nele,
    porque as duas coisas não compartilham nada além de título e imagem: um
    projeto tem tecnologias, repositório, deploy e vídeo; uma vivência tem
    papel e período. Enfiar as duas na mesma tabela deixaria metade dos campos
    sempre vazios, e o admin pediria ao André que ignorasse os que não valem
    para o que ele está cadastrando.

    Alimenta a segunda face do site (`data-tema="azul"`), que só aparece
    quando alguém clica em "Conheça o André fora da sua área".
    """

    titulo = models.CharField('título', max_length=120)
    slug = models.SlugField('identificador', max_length=140, unique=True, blank=True)
    papel = models.CharField(
        'papel',
        max_length=120,
        blank=True,
        help_text='O que você era ali. Ex.: "Representante de sala", "Membro".',
    )
    periodo = models.CharField(
        'período',
        max_length=60,
        blank=True,
        help_text='Texto livre, do jeito que faz sentido para esta atividade: '
                  '"2025", "2024 — 2025", "2º semestre de 2025".',
    )
    descricao_curta = models.CharField(
        'descrição curta',
        max_length=200,
        help_text='Uma ou duas linhas. É o que aparece no cartão — o limite de '
                  '200 caracteres existe para os cartões da grade ficarem da '
                  'mesma altura.',
    )
    descricao = models.TextField(
        'descrição completa',
        blank=True,
        help_text='Opcional. Aparece no botão "Detalhes" do cartão. Sem ela, o '
                  'botão não é desenhado.',
    )
    imagem = models.ImageField(
        'imagem',
        upload_to='vivencias/',
        blank=True,
        help_text='Proporção 16:9 fica melhor no cartão. Sem imagem, o cartão '
                  'mostra a malha técnica no lugar.',
    )
    publicado = models.BooleanField(
        'publicado',
        default=True,
        help_text='Desmarque para esconder do site sem apagar o cadastro.',
    )
    ordem_exibicao = models.PositiveIntegerField('ordem de exibição', default=0)

    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'vivência'
        verbose_name_plural = 'vivências'
        # Sem `destaque` como em `Projeto`: são cinco ou seis atividades numa
        # grade só, e a ordem manual dá conta. O título desempata para a lista
        # não dançar quando várias ficam na ordem 0.
        ordering = ['ordem_exibicao', 'titulo']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)


class Certificado(models.Model):
    class Categoria(models.TextChoices):
        PROGRAMACAO = 'programacao', 'Programação'
        WEB = 'web', 'Desenvolvimento web'
        REQUISITOS = 'requisitos', 'Análise e requisitos'
        DADOS = 'dados', 'Dados'
        OUTROS = 'outros', 'Outros'

    nome = models.CharField('nome do curso', max_length=180)
    instituicao_emissora = models.CharField('instituição emissora', max_length=120)
    data_emissao = models.DateField('data de emissão')
    carga_horaria = models.PositiveIntegerField(
        'carga horária',
        null=True,
        blank=True,
        help_text='Em horas. Deixe vazio se o certificado não informa.',
    )
    link_credencial = models.URLField(
        'link de verificação',
        blank=True,
        help_text='Endereço público onde a credencial pode ser conferida.',
    )
    arquivo_pdf = models.FileField(
        'arquivo PDF',
        upload_to='certificados/',
        storage=storage_de_arquivo,
        blank=True,
    )
    categoria = models.CharField(
        'categoria',
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.OUTROS,
    )
    ordem_exibicao = models.PositiveIntegerField('ordem de exibição', default=0)

    class Meta:
        verbose_name = 'certificado'
        verbose_name_plural = 'certificados'
        ordering = ['ordem_exibicao', '-data_emissao']

    def __str__(self):
        return f'{self.nome} — {self.instituicao_emissora}'

    @property
    def tem_verificacao(self):
        return bool(self.link_credencial or self.arquivo_pdf)


class Experiencia(models.Model):
    """Uma entrada da linha do tempo: um emprego ou uma formação."""

    class Tipo(models.TextChoices):
        EXPERIENCIA = 'experiencia', 'Experiência profissional'
        EDUCACAO = 'educacao', 'Formação acadêmica'

    tipo = models.CharField('tipo', max_length=20, choices=Tipo.choices)
    cargo = models.CharField(
        'cargo ou curso',
        max_length=140,
        help_text='Ex.: "Estagiário de TI — Desenvolvimento de Software" ou '
                  '"Engenharia de Software".',
    )
    organizacao = models.CharField('organização', max_length=140)
    local = models.CharField('local', max_length=80, blank=True)
    data_inicio = models.DateField('início')
    data_fim = models.DateField(
        'término',
        null=True,
        blank=True,
        help_text='Deixe vazio para a entrada aparecer como "Atual".',
    )
    descricao = models.TextField(
        'descrição',
        blank=True,
        help_text='Uma atividade por linha. Cada linha vira um item da lista.',
    )
    ordem_exibicao = models.PositiveIntegerField('ordem de exibição', default=0)

    class Meta:
        verbose_name = 'experiência'
        verbose_name_plural = 'experiências e formação'
        ordering = ['ordem_exibicao', '-data_inicio']

    def __str__(self):
        return f'{self.cargo} — {self.organizacao}'

    @property
    def em_curso(self):
        return self.data_fim is None

    @property
    def periodo(self):
        """"10/2025 — Atual" ou "2025 — 2028"."""
        inicio = self.data_inicio.strftime('%m/%Y')
        if self.em_curso:
            return f'{inicio} — Atual'
        return f'{inicio} — {self.data_fim.strftime("%m/%Y")}'

    @property
    def atividades(self):
        """A descrição quebrada em linhas, para virar <li>."""
        return [linha.strip() for linha in self.descricao.splitlines() if linha.strip()]


class MensagemContato(models.Model):
    """
    O que o formulário de contato recebe.

    Existe para que uma falha de SMTP não custe um contato: a view grava a
    mensagem ANTES de tentar enviar o e-mail, e `email_enviado` registra se o
    envio deu certo. Sem isto, um endereço errado no .env significaria
    mensagens perdidas sem ninguém saber.
    """

    nome = models.CharField('nome', max_length=120)
    email = models.EmailField('e-mail')
    assunto = models.CharField('assunto', max_length=160, blank=True)
    mensagem = models.TextField('mensagem')

    # Indexado porque esta é a ÚNICA tabela do projeto que cresce sem limite —
    # as outras têm o tamanho do currículo. E o admin a ordena por
    # `-enviada_em` com `date_hierarchy`, que varre a coluna inteira para
    # montar a navegação por ano/mês.
    enviada_em = models.DateTimeField('recebida em', auto_now_add=True, db_index=True)
    lida = models.BooleanField('lida', default=False)
    email_enviado = models.BooleanField(
        'e-mail entregue',
        default=False,
        help_text='Falso significa que o SMTP falhou. A mensagem está aqui de '
                  'qualquer forma.',
    )

    class Meta:
        verbose_name = 'mensagem de contato'
        verbose_name_plural = 'mensagens de contato'
        ordering = ['-enviada_em']

    def __str__(self):
        return f'{self.nome} <{self.email}>'
