from django.http import Http404
from django.shortcuts import render

from .models import Device
from .services import cargar_dispositivos, listar_zonas_con_resumen, obtener_zona_detalle


def _organization_id(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        return profile.organization_id if profile else None
    return None


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
    dispositivos = cargar_dispositivos(_organization_id(request))
    activos = sum(1 for item in dispositivos if item.get("estado") == Device.STATUS_ACTIVE)
    contexto = {
        "dispositivos": dispositivos,
        "total": len(dispositivos),
        "total_activos": activos,
    }
    return render(request, "dispositivos/catalogo.html", contexto)


def zonas(request):
    zonas = listar_zonas_con_resumen(_organization_id(request))
    return render(request, "dispositivos/zonas.html", {"zonas": zonas})


def zona_detalle(request, zona_id):
    detalle = obtener_zona_detalle(zona_id, _organization_id(request))
    if detalle is None:
        raise Http404("Zona no encontrada")

    return render(request, "dispositivos/zona_detalle.html", detalle)

def resumen_zonas(request, zona_id=None):
    if zona_id is not None:
        detalle = obtener_zona_detalle(zona_id, _organization_id(request))
        if detalle is None:
            raise Http404("Zona no encontrada")
        return render(request, "dispositivos/resumen_zonas.html", detalle)

    zonas = listar_zonas_con_resumen(_organization_id(request))
    return render(request, "dispositivos/resumen_zonas.html", {"zonas": zonas})
