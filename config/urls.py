from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

handler403 = 'dispositivos.views.custom_403'
handler404 = 'dispositivos.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('dispositivos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
