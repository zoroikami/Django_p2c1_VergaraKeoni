from django.db.models import Count, F, Q, Sum

from .models import Device, Zone


def cargar_dispositivos(organization_id=None):
    queryset = Device.objects.filter(deleted_at__isnull=True)
    if organization_id is not None:
        queryset = queryset.filter(organization_id=organization_id)
    return list(
        queryset
        .select_related("category", "zone", "organization")
        .values(
            "id",
            "serial_number",
            nombre=F("name"),
            estado=F("status"),
            consumo_kwh=F("consumption_kwh"),
            zona_id=F("zone_id"),
            categoria_id=F("category_id"),
            categoria=F("category__name"),
            zona=F("zone__name"),
        )
    )


def obtener_zona_detalle(zona_id, organization_id=None):
    zones = Zone.objects.filter(id=zona_id, deleted_at__isnull=True)
    if organization_id is not None:
        zones = zones.filter(organization_id=organization_id)
    zona = zones.first()
    if zona is None:
        return None

    dispositivos_zona = [
        {
            "id": dispositivo.id,
            "nombre": dispositivo.name,
            "consumo_kwh": float(dispositivo.consumption_kwh),
            "categoria": dispositivo.category.name,
        }
        for dispositivo in Device.objects.filter(
            zone=zona, deleted_at__isnull=True
        ).select_related("category")
    ]

    consumo_total = sum(item["consumo_kwh"] for item in dispositivos_zona)
    estado = "ALERTA" if consumo_total > float(zona.limit_kwh) else "NORMAL"

    return {
        "zona": {
            "id": zona.id,
            "nombre": zona.name,
            "limite_kwh": float(zona.limit_kwh),
        },
        "dispositivos": dispositivos_zona,
        "consumo_total": consumo_total,
        "estado": estado,
        "cantidad_dispositivos": len(dispositivos_zona),
    }


def listar_zonas_con_resumen(organization_id=None):
    zones = Zone.objects.filter(deleted_at__isnull=True)
    if organization_id is not None:
        zones = zones.filter(organization_id=organization_id)
    resumen = zones.annotate(
        cantidad_dispositivos=Count("devices", filter=Q(devices__deleted_at__isnull=True)),
        consumo_total=Sum("devices__consumption_kwh", filter=Q(devices__deleted_at__isnull=True)),
    )
    return [
        {
            "id": zona.id,
            "nombre": zona.name,
            "limite_kwh": float(zona.limit_kwh),
            "cantidad_dispositivos": zona.cantidad_dispositivos,
            "consumo_total": float(zona.consumo_total or 0),
            "estado": "ALERTA" if (zona.consumo_total or 0) > zona.limit_kwh else "NORMAL",
        }
        for zona in resumen
    ]
