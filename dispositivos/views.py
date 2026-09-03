from django.http import Http404
from django.shortcuts import render

from .services import cargar_dispositivos, listar_zonas_con_resumen, obtener_zona_detalle


def custom_404(request, exception):
    return render(request, "404.html", status=404)


def inicio(request):
    contexto = {
        "sistema": "EcoEnergy",
        "mensaje": "Monitoreo energético responsable",
        "asignatura": "Programación Back End",
    }
    return render(request, "dispositivos/inicio.html", contexto)


def catalogo(request):
    dispositivos = cargar_dispositivos()
    activos = sum(1 for item in dispositivos if item.get("estado") == "Activo")
    contexto = {
        "dispositivos": dispositivos,
        "total": len(dispositivos),
        "total_activos": activos,
    }
    return render(request, "dispositivos/catalogo.html", contexto)


def zonas(request):
    zonas = listar_zonas_con_resumen()
    return render(request, "dispositivos/zonas.html", {"zonas": zonas})


def zona_detalle(request, zona_id):
    detalle = obtener_zona_detalle(zona_id)
    if detalle is None:
        raise Http404("Zona no encontrada")

    return render(request, "dispositivos/zona_detalle.html", detalle)

def resumen_zonas(request):
    detalle =  listar_zonas_con_resumen()
    if detalle is None:
        raise Http404("Zona no encontrada")
    
    return render(request, "dispositivos/resumen_zonas.html", {"zonas": zonas})

def catalogo(request):
    dispositivos = cargar_dispositivos()
    activos = sum(1 for item in dispositivos if item.get("estado") == "Activo")
    contexto = {
        "dispositivos": dispositivos,
        "total": len(dispositivos),
        "total_activos": activos,
    }
    return render(request, "dispositivos/resumen_zonas.html", contexto)
