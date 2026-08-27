from django.urls import path
from . import views

app_name = "dispositivos"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("dispositivos/", views.catalogo, name="catalogo"),
]
