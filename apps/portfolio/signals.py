"""
Limpeza do cache da home quando o conteúdo muda.

A home é cacheada (`views.TEMPO_DE_CACHE_DA_HOME`) porque montá-la custa sete
consultas × ~155ms de latência até o Supabase. Sem isto, editar um projeto no
admin e recarregar o site mostraria a versão velha por até quinze minutos — e
não há sintoma pior num painel de administração do que salvar, conferir, e ver
o valor antigo. A pessoa salva de novo. E de novo.

`cache.clear()` e não uma chave cirúrgica: a chave que o `cache_page` monta
inclui o método, o caminho e os cabeçalhos do `Vary`, e reconstruí-la à mão
significaria copiar um detalhe interno do Django que muda entre versões — o
tipo de acoplamento que quebra calado num upgrade. Como o cache guarda uma
página só, limpar tudo é exatamente equivalente e não depende de nada interno.
"""

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .models import Certificado, Experiencia, Projeto, Tecnologia

# `MensagemContato` fica de fora: ela não aparece na home. Uma mensagem de
# contato recebida não deve invalidar nada — e é justamente o modelo que mais
# recebe escrita.
MODELOS_DA_HOME = (Projeto, Certificado, Experiencia, Tecnologia)


@receiver(post_save)
@receiver(post_delete)
def limpar_cache_da_home(sender, **kwargs):
    if sender in MODELOS_DA_HOME:
        cache.clear()


@receiver(m2m_changed, sender=Projeto.tecnologias.through)
def limpar_cache_ao_mudar_tecnologias(sender, action, **kwargs):
    """
    Trocar as tecnologias de um projeto NÃO dispara `post_save`.

    O Django grava a tabela intermediária por fora do `save()` do modelo, então
    o receptor acima nunca veria essa alteração — e ela é visível na home em
    dois lugares: as pílulas do cartão e a barra de filtros, que só lista
    tecnologia de projeto publicado. Sem isto, tirar a última tecnologia de um
    projeto deixaria a pílula órfã no filtro até o TTL expirar.

    Só as ações que de fato mudam o vínculo; `pre_*` viria antes da escrita.
    """
    if action in ('post_add', 'post_remove', 'post_clear'):
        cache.clear()
