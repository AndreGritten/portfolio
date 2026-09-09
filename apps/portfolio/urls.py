from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.home, name='home'),
    path('contato/', views.contato, name='contato'),
    path('curriculo/', views.curriculo, name='curriculo'),
    # Sem app_name/namespace por simplicidade — é infraestrutura (healthcheck
    # do Fly.io), não navegação do site, então não precisa de `{% url %}` em
    # template nenhum. Ver views.saude para o porquê de existir.
    path('saude/', views.saude, name='saude'),
]
