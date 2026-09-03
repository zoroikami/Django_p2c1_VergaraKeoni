import json
from django.conf import settings


def _cargar_json(nombre_archivo):
    ruta = settings.BASE_DIR / "data" / nombre_archivo
    with ruta.open(encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if not isinstance(datos, list):
        raise ValueError(f"Se esperaba una lista en {nombre_archivo}")
    return datos


def cargar_dispositivos():
    return _cargar_json("dispositivos.json")


def cargar_zonas():
    return _cargar_json("zonas.json")


def cargar_categorias():
    return _cargar_json("categorias.json")


def obtener_zona_detalle(zona_id):
    zonas = cargar_zonas()
    zona = next((item for item in zonas if item["id"] == zona_id), None)
    if zona is None:
        return None

    dispositivos = cargar_dispositivos()
    categorias = {item["id"]: item for item in cargar_categorias()}

    dispositivos_zona = [
        {
            "id": dispositivo["id"],
            "nombre": dispositivo["nombre"],
            "consumo_kwh": float(dispositivo.get("consumo_kwh", 0)),
            "categoria": categorias.get(dispositivo.get("categoria_id"), {"nombre": "Sin categoría"})["nombre"],
        }
        for dispositivo in dispositivos
        if dispositivo.get("zona_id") == zona_id
    ]

    consumo_total = sum(item["consumo_kwh"] for item in dispositivos_zona)
    estado = "ALERTA" if consumo_total > float(zona.get("limite_kwh", 0)) else "NORMAL"

    return {
        "zona": zona,
        "dispositivos": dispositivos_zona,
        "consumo_total": consumo_total,
        "estado": estado,
        "cantidad_dispositivos": len(dispositivos_zona),
    }


def listar_zonas_con_resumen():
    zonas = cargar_zonas()
    dispositivos = cargar_dispositivos()
    resumen = []

    for zona in zonas:
        zona_id = zona["id"]
        zona_dispositivos = [
            item for item in dispositivos if item.get("zona_id") == zona_id
        ]
        consumo_total = sum(float(item.get("consumo_kwh", 0)) for item in zona_dispositivos)
        estado = "ALERTA" if consumo_total > float(zona.get("limite_kwh", 0)) else "NORMAL"
        resumen.append(
            {
                "id": zona_id,
                "nombre": zona["nombre"],
                "limite_kwh": float(zona.get("limite_kwh", 0)),
                "cantidad_dispositivos": len(zona_dispositivos),
                "consumo_total": consumo_total,
                "estado": estado,
            }
        )

    return resumen
