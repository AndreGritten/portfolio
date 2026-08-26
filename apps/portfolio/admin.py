"""
O admin é a única interface de edição do site — então ele precisa ser
confortável, não apenas funcional.

Três decisões que valem explicação:

1. `list_editable` na ordem de exibição: reordenar a página inteira sem abrir
   um formulário por vez é a operação mais frequente aqui.
2. Miniatura na listagem de projetos: sem ela, distinguir dois projetos com
   nomes parecidos exige abrir os dois.
3. `MensagemContato` é somente leitura. Ela é registro do que chegou; poder
   editar o texto de uma mensagem recebida não serve a nada e destrói a única
   garantia que ela oferece.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Certificado, Experiencia, MensagemContato, Projeto, Tecnologia

admin.site.site_header = 'Portfólio · André Gritten'
admin.site.site_title = 'Portfólio'
admin.site.index_title = 'Conteúdo do site'


@admin.register(Tecnologia)
class TecnologiaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'ordem', 'total_projetos')
    list_editable = ('categoria', 'ordem')
    list_filter = ('categoria',)
    search_fields = ('nome',)
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ('categoria', 'ordem', 'nome')

    @admin.display(description='projetos')
    def total_projetos(self, obj):
        return obj.projetos.count()


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = (
        'miniatura',
        'titulo',
        'tecnologias_resumidas',
        'destaque',
        'publicado',
        'ordem_exibicao',
    )
    # `titulo` não entra em list_editable: o primeiro campo da listagem é o
    # link para o formulário, e o Django recusa editá-lo em linha.
    list_editable = ('destaque', 'publicado', 'ordem_exibicao')
    list_filter = ('publicado', 'destaque', 'tecnologias')
    search_fields = ('titulo', 'descricao_curta', 'descricao')
    prepopulated_fields = {'slug': ('titulo',)}
    filter_horizontal = ('tecnologias',)
    readonly_fields = ('criado_em', 'atualizado_em', 'previa')

    fieldsets = (
        ('Identificação', {
            'fields': ('titulo', 'slug'),
        }),
        ('Conteúdo', {
            'fields': ('descricao_curta', 'descricao', 'imagem', 'previa', 'tecnologias'),
        }),
        ('Links', {
            'fields': ('link_github', 'link_deploy'),
        }),
        ('Exibição', {
            'fields': ('destaque', 'publicado', 'ordem_exibicao'),
            'description': 'Projetos em destaque aparecem primeiro; entre eles '
                           'vale a ordem de exibição, do menor para o maior.',
        }),
        ('Registro', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        # Sem isto, `tecnologias_resumidas` dispara uma consulta por linha da
        # listagem.
        return super().get_queryset(request).prefetch_related('tecnologias')

    @admin.display(description='')
    def miniatura(self, obj):
        if not obj.imagem:
            return '—'
        return format_html(
            '<img src="{}" style="height:34px;width:60px;object-fit:cover;'
            'border-radius:4px;" alt="">',
            obj.imagem.url,
        )

    @admin.display(description='prévia da imagem')
    def previa(self, obj):
        if not obj.imagem:
            return 'Nenhuma imagem enviada.'
        return format_html(
            '<img src="{}" style="max-width:420px;height:auto;border-radius:8px;" alt="">',
            obj.imagem.url,
        )

    @admin.display(description='tecnologias')
    def tecnologias_resumidas(self, obj):
        nomes = [t.nome for t in obj.tecnologias.all()]
        if not nomes:
            return '—'
        if len(nomes) <= 3:
            return ', '.join(nomes)
        return f'{", ".join(nomes[:3])} +{len(nomes) - 3}'


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'instituicao_emissora',
        'data_emissao',
        'carga_horaria',
        'verificacao',
        'ordem_exibicao',
    )
    list_editable = ('ordem_exibicao',)
    list_filter = ('instituicao_emissora', 'categoria')
    search_fields = ('nome', 'instituicao_emissora')
    date_hierarchy = 'data_emissao'

    fieldsets = (
        ('Certificado', {
            'fields': ('nome', 'instituicao_emissora', 'categoria'),
        }),
        ('Dados', {
            'fields': ('data_emissao', 'carga_horaria'),
        }),
        ('Comprovação', {
            'fields': ('link_credencial', 'arquivo_pdf'),
            'description': 'Um dos dois basta. Sem nenhum, o cartão aparece '
                           'sem botão de verificação.',
        }),
        ('Exibição', {
            'fields': ('ordem_exibicao',),
        }),
    )

    @admin.display(description='verificação')
    def verificacao(self, obj):
        if obj.link_credencial:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">credencial</a>',
                obj.link_credencial,
            )
        if obj.arquivo_pdf:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">PDF</a>',
                obj.arquivo_pdf.url,
            )
        return '—'


@admin.register(Experiencia)
class ExperienciaAdmin(admin.ModelAdmin):
    list_display = ('cargo', 'organizacao', 'tipo', 'periodo', 'ordem_exibicao')
    list_editable = ('ordem_exibicao',)
    list_filter = ('tipo',)
    search_fields = ('cargo', 'organizacao', 'descricao')

    fieldsets = (
        ('Entrada', {
            'fields': ('tipo', 'cargo', 'organizacao', 'local'),
        }),
        ('Período', {
            'fields': ('data_inicio', 'data_fim'),
            'description': 'Término vazio marca a entrada como "Atual" — o '
                           'marcador da linha do tempo fica preenchido.',
        }),
        ('Atividades', {
            'fields': ('descricao',),
            'description': 'Uma atividade por linha. Cada linha vira um item '
                           'da lista no site.',
        }),
        ('Exibição', {
            'fields': ('ordem_exibicao',),
        }),
    )

    @admin.display(description='período')
    def periodo(self, obj):
        return obj.periodo


@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'assunto', 'enviada_em', 'lida', 'email_enviado')
    list_filter = ('lida', 'email_enviado', 'enviada_em')
    search_fields = ('nome', 'email', 'assunto', 'mensagem')
    date_hierarchy = 'enviada_em'
    actions = ('marcar_como_lida', 'marcar_como_nao_lida')

    readonly_fields = (
        'nome', 'email', 'assunto', 'mensagem', 'enviada_em', 'email_enviado',
    )

    # Registro do que chegou: não se cria à mão e não se reescreve. Apagar
    # continua permitido — é o que limpa spam que passou pelo honeypot.
    def has_add_permission(self, request):
        return False

    @admin.action(description='Marcar como lida')
    def marcar_como_lida(self, request, queryset):
        total = queryset.update(lida=True)
        self.message_user(request, f'{total} mensagem(ns) marcada(s) como lida(s).')

    @admin.action(description='Marcar como não lida')
    def marcar_como_nao_lida(self, request, queryset):
        total = queryset.update(lida=False)
        self.message_user(request, f'{total} mensagem(ns) marcada(s) como não lida(s).')
