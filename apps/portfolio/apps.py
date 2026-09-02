from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portfolio'
    verbose_name = 'Portfólio'

    def ready(self):
        # Importar por efeito colateral é o jeito documentado de registrar
        # receptores de signal: o `@receiver` só passa a valer quando o módulo
        # é lido, e `ready()` é o único ponto em que o Django garante que os
        # modelos já existem.
        from . import signals  # noqa: F401
