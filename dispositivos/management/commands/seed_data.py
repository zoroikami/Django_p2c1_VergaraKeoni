from django.core.management.base import BaseCommand

from dispositivos.models import Category, Device, Organization, Zone


class Command(BaseCommand):
    help = "Carga datos de demostracion de EcoEnergy de forma reproducible."

    def handle(self, *args, **options):
        organization, _ = Organization.objects.update_or_create(
            tax_id="76.123.456-7",
            defaults={
                "legal_name": "EcoEnergy Demo SpA",
                "trade_name": "EcoEnergy Demo",
                "contact": "demo@ecoenergy.local",
                "is_active": True,
            },
        )

        categories = {
            name: Category.objects.update_or_create(
                name=name,
                defaults={"description": description, "is_active": True},
            )[0]
            for name, description in {
                "Iluminacion": "Dispositivos de iluminacion y control de energia",
                "Climatizacion": "Equipos de aire acondicionado y ventilacion",
                "Monitoreo": "Sensores y medidores inteligentes",
            }.items()
        }

        zones = {
            name: Zone.objects.update_or_create(
                organization=organization,
                name=name,
                defaults={"limit_kwh": limit, "is_active": True},
            )[0]
            for name, limit in {
                "Zona Norte": 120.50,
                "Zona Sur": 180.00,
                "Zona Centro": 210.25,
            }.items()
        }

        devices = (
            ("Medidor inteligente", "SN-001", "Monitoreo", "Zona Norte", 18.40),
            ("Luminaria inteligente", "SN-002", "Iluminacion", "Zona Norte", 12.10),
            ("Climatizador", "SN-003", "Climatizacion", "Zona Sur", 32.70),
            ("Sensor de temperatura", "SN-004", "Monitoreo", "Zona Sur", 8.90),
            ("Panel LED", "SN-005", "Iluminacion", "Zona Centro", 15.50),
            ("Aire acondicionado", "SN-006", "Climatizacion", "Zona Centro", 41.20),
            ("Medidor de energia", "SN-007", "Monitoreo", "Zona Norte", 24.30),
            ("Bombillo ahorrador", "SN-008", "Iluminacion", "Zona Sur", 10.60),
        )
        for name, serial, category, zone, consumption in devices:
            Device.objects.update_or_create(
                serial_number=serial,
                defaults={
                    "name": name,
                    "organization": organization,
                    "category": categories[category],
                    "zone": zones[zone],
                    "status": Device.STATUS_ACTIVE,
                    "consumption_kwh": consumption,
                },
            )

        self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
