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

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Case, IntegerField, Value, When
from django.utils.text import slugify


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
        esse valor é alfabético: backend, database, engenharia, ferramentas,
        frontend. O quadro saía com Frontend depois de Ferramentas — fora da
        sequência que a pessoa espera (o que roda no servidor, os dados, o que
        aparece na tela, o método, as ferramentas) e, com cinco colunas numa
        grade de quatro, sozinho numa segunda linha.

        Um `Case` resolve sem tocar no que está gravado. A alternativa seria
        renomear os valores para 'a-backend', 'b-database'… — uma migração e
        um dado feio para sempre, só para agradar a um ORDER BY.
        """
        pesos = [
            When(categoria=valor, then=Value(indice))
            for indice, valor in enumerate(self.model.ORDEM_DO_QUADRO)
        ]
        return self.alias(
            peso=Case(*pesos, default=Value(99), output_field=IntegerField())
        ).order_by('peso', 'ordem', 'nome')


class Tecnologia(models.Model):
    """Uma tag técnica. Alimenta o filtro de projetos e o quadro de habilidades."""

    class Categoria(models.TextChoices):
        BACKEND = 'backend', 'Backend'
        DATABASE = 'database', 'Banco de dados'
        FRONTEND = 'frontend', 'Frontend'
        ENGENHARIA = 'engenharia', 'Engenharia e metodologias'
        FERRAMENTAS = 'ferramentas', 'Ferramentas'

    # A ordem das colunas na seção de habilidades. Uma categoria nova que não
    # entre nesta lista cai no fim, o que é o comportamento certo: aparece,
    # sem se meter no meio de uma sequência pensada.
    ORDEM_DO_QUADRO = [
        Categoria.BACKEND,
        Categoria.DATABASE,
        Categoria.FRONTEND,
        Categoria.ENGENHARIA,
        Categoria.FERRAMENTAS,
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
        default=Categoria.BACKEND,
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
    def slugs_tecnologias(self):
        """
        Os slugs separados por espaço, para o atributo `data-tecnologias`.

        O filtro roda no navegador, sem recarregar a página: os cartões já
        chegam renderizados e o Alpine só decide quais mostrar.
        """
        return ' '.join(t.slug for t in self.tecnologias.all())


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
