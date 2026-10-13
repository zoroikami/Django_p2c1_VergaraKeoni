from django.urls import path
from . import views

app_name = "dispositivos"

urlpatterns = [
    # Inicio y resumen
    path("", views.inicio, name="inicio"),
    
    # CRUD Protegido de Dispositivos (Clases 7 y 8)
    path("dispositivos/", views.DeviceListView.as_view(), name="catalogo"),
    path("dispositivos/new/", views.DeviceCreateView.as_view(), name="device_create"),
    path("dispositivos/<int:pk>/edit/", views.DeviceUpdateView.as_view(), name="device_update"),
    path("dispositivos/<int:pk>/delete/", views.DeviceDeleteView.as_view(), name="device_delete"),

    # Zonas y resumen
    path("zonas/", views.zonas, name="zonas"),
    path("zonas/<int:zona_id>/", views.zona_detalle, name="zona_detalle"),
    path("dispositivos/resumen_zonas/<int:zona_id>/", views.resumen_zonas, name="resumen_zonas"),
    path("dispositivos/resumen_zonas/", views.resumen_zonas, name="resumen_zonas"),

    # Desafío: Recuperación de contraseña con código temporal de 6 dígitos (Clase 6)
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("password-reset/verify/", views.password_reset_verify, name="password_reset_verify"),
    path("password-reset/confirm/", views.password_reset_confirm, name="password_reset_confirm"),
]
