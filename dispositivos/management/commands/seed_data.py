from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from dispositivos.models import (
    Category,
    Department,
    Device,
    Measurement,
    Organization,
    UserProfile,
    Zone,
)
from dispositivos.roles import (
    ROLE_ADMIN_ORG,
    ROLE_CONSULTA,
    ROLE_OPERADOR,
    setup_roles_and_permissions,
)


class Command(BaseCommand):
    help = "Carga datos de demostracion de EcoEnergy multi-organizacion (Norte y Sur) para comprobar scoping y seguridad (Clase 5)."

    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write("Configurando grupos y roles...")
        setup_roles_and_permissions()

        # 1. Superusuario global
        superuser, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@ecoenergy.local", "is_staff": True, "is_superuser": True},
        )
        superuser.set_password("Admin123!")
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save()

        # 2. Categorias comunes
        categories = {}
        cat_data = {
            "Monitoreo": "Sensores y medidores inteligentes de energia",
            "Iluminacion": "Sistemas de luminarias LED inteligentes",
            "Climatizacion": "Equipos de climatizacion y ventilacion eficiente",
        }
        for name, desc in cat_data.items():
            cat, _ = Category.objects.update_or_create(
                name=name,
                defaults={"description": desc, "is_active": True},
            )
            categories[name] = cat

        # 3. Organizaciones (Norte y Sur para aislamiento de datos)
        org_configs = [
            {
                "tax_id": "76.111.111-1",
                "legal_name": "EcoEnergy Norte SpA",
                "trade_name": "EcoEnergy Norte",
                "contact": "contacto@norte.ecoenergy.local",
                "depts": ["Operaciones Norte", "Mantenimiento Norte"],
                "zones": [
                    ("Zona Interior Norte", 150.0),
                    ("Zona Exterior Norte", 80.0),
                ],
                "devices": [
                    ("Medidor Principal Norte", "SN-NTE-001", "Monitoreo", "Zona Interior Norte", 22.50),
                    ("Luminaria Bodega Norte", "SN-NTE-002", "Iluminacion", "Zona Interior Norte", 14.20),
                    ("Climatizador Central Norte", "SN-NTE-003", "Climatizacion", "Zona Exterior Norte", 35.80),
                    ("Sensor Consumo Norte", "SN-NTE-004", "Monitoreo", "Zona Exterior Norte", 9.10),
                ],
                "users": [
                    ("admin_norte", "Admin", "Norte", ROLE_ADMIN_ORG, "11.111.111-1"),
                    ("operador_norte", "Carlos", "Norte", ROLE_OPERADOR, "12.222.222-2"),
                    ("consulta_norte", "Lucia", "Norte", ROLE_CONSULTA, "13.333.333-3"),
                ],
            },
            {
                "tax_id": "76.222.222-2",
                "legal_name": "EcoEnergy Sur SpA",
                "trade_name": "EcoEnergy Sur",
                "contact": "contacto@sur.ecoenergy.local",
                "depts": ["Operaciones Sur", "Mantenimiento Sur"],
                "zones": [
                    ("Zona Planta Sur", 220.0),
                    ("Zona Almacen Sur", 110.0),
                ],
                "devices": [
                    ("Medidor Principal Sur", "SN-SUR-001", "Monitoreo", "Zona Planta Sur", 45.10),
                    ("Luminaria Planta Sur", "SN-SUR-002", "Iluminacion", "Zona Planta Sur", 18.30),
                    ("Climatizador Camara Sur", "SN-SUR-003", "Climatizacion", "Zona Almacen Sur", 52.00),
                    ("Sensor Humedad Sur", "SN-SUR-004", "Monitoreo", "Zona Almacen Sur", 6.40),
                ],
                "users": [
                    ("admin_sur", "Admin", "Sur", ROLE_ADMIN_ORG, "21.111.111-1"),
                    ("operador_sur", "Marta", "Sur", ROLE_OPERADOR, "22.222.222-2"),
                    ("consulta_sur", "Pedro", "Sur", ROLE_CONSULTA, "23.333.333-3"),
                ],
            },
        ]

        now = timezone.now()
        for org_conf in org_configs:
            org, _ = Organization.objects.update_or_create(
                tax_id=org_conf["tax_id"],
                defaults={
                    "legal_name": org_conf["legal_name"],
                    "trade_name": org_conf["trade_name"],
                    "contact": org_conf["contact"],
                    "is_active": True,
                },
            )

            # Departamentos
            departments = {}
            for d_name in org_conf["depts"]:
                dept, _ = Department.objects.update_or_create(
                    organization=org,
                    name=d_name,
                    defaults={"description": f"Departamento {d_name}", "is_active": True},
                )
                departments[d_name] = dept

            # Zonas
            zones = {}
            for z_name, limit in org_conf["zones"]:
                zone, _ = Zone.objects.update_or_create(
                    organization=org,
                    name=z_name,
                    defaults={"limit_kwh": limit, "is_active": True},
                )
                zones[z_name] = zone

            # Usuarios y perfiles
            first_dept = list(departments.values())[0]
            for username, fname, lname, role_name, rut in org_conf["users"]:
                u, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@ecoenergy.local",
                        "first_name": fname,
                        "last_name": lname,
                        "is_staff": True,
                        "is_active": True,
                    },
                )
                u.set_password("Password123!")
                u.is_staff = True
                u.is_active = True
                u.save()

                group = Group.objects.get(name=role_name)
                u.groups.set([group])

                UserProfile.objects.update_or_create(
                    user=u,
                    defaults={
                        "organization": org,
                        "department": first_dept,
                        "rut": rut,
                        "phone": "+56987654321",
                    },
                )

            # Dispositivos y mediciones
            for name, serial, cat_name, z_name, cons in org_conf["devices"]:
                dev, _ = Device.objects.update_or_create(
                    serial_number=serial,
                    defaults={
                        "name": name,
                        "organization": org,
                        "category": categories[cat_name],
                        "zone": zones[z_name],
                        "status": Device.STATUS_ACTIVE,
                        "consumption_kwh": cons,
                    },
                )

                # Medicion de ejemplo
                Measurement.objects.get_or_create(
                    device=dev,
                    measured_at=now,
                    defaults={
                        "value_kwh": cons,
                        "unit": "kWh",
                        "source": Measurement.SOURCE_AUTOMATIC,
                        "integration_name": "API-IoT-Gateway",
                    },
                )

        # 4. Usuario staff sin perfil (caso de prueba negativa de scoping)
        staff_unassigned, _ = User.objects.get_or_create(
            username="staff_sin_perfil",
            defaults={"email": "unassigned@ecoenergy.local", "is_staff": True, "is_active": True},
        )
        staff_unassigned.set_password("Password123!")
        staff_unassigned.is_staff = True
        staff_unassigned.is_active = True
        staff_unassigned.save()
        UserProfile.objects.filter(user=staff_unassigned).delete()

        self.stdout.write(self.style.SUCCESS("Datos de demostracion cargados exitosamente."))
        self.stdout.write("Credenciales disponibles (clave general: 'Password123!'):")
        self.stdout.write(" - Superusuario: 'admin' (clave: Admin123!)")
        self.stdout.write(" - Norte: 'admin_norte', 'operador_norte', 'consulta_norte'")
        self.stdout.write(" - Sur: 'admin_sur', 'operador_sur', 'consulta_sur'")
        self.stdout.write(" - Sin perfil: 'staff_sin_perfil'")
