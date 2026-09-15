from django.urls import path
from . import views

app_name = "dispositivos"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("dispositivos/", views.catalogo, name="catalogo"),
    path("zonas/", views.zonas, name="zonas"),
    path("zonas/<int:zona_id>/", views.zona_detalle, name="zona_detalle"),
    path("dispositivos/resumen_zonas/<int:zona_id>/", views.resumen_zonas, name="resumen_zonas"),
    path("dispositivos/resumen_zonas/", views.resumen_zonas, name="resumen_zonas"),
]
