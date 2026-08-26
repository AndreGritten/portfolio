"""Rotas do projeto."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('jarvis/', admin.site.urls),
    path('', include('apps.portfolio.urls')),
]

# Em desenvolvimento o próprio runserver entrega o que está em MEDIA_ROOT.
# Em produção quem serve é o Cloudinary, então esta rota não existe — e não
# deve existir: `static()` não é feito para produção e ignoraria as regras de
# cache do WhiteNoise.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
