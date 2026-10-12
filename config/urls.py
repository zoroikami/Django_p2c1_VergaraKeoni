from django.contrib import admin
from django.urls import path, include

handler403 = 'dispositivos.views.custom_403'
handler404 = 'dispositivos.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('dispositivos.urls')),
]
