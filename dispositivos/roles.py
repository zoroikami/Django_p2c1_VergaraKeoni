from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from dispositivos.models import Department, Organization, UserProfile

ROLE_ADMIN_ORG = "Administrador Organizacional"
ROLE_OPERADOR = "Operador"
ROLE_CONSULTA = "Consulta"

# Matriz de permisos segun el principio de menor privilegio (Clase 4)
ROLE_PERMISSIONS = {
    ROLE_ADMIN_ORG: [
        # Configuracion y gestion operativa completa (sin borrado fisico)
        ("category", ["add_category", "change_category", "view_category"]),
        ("zone", ["add_zone", "change_zone", "view_zone"]),
        ("device", ["add_device", "change_device", "view_device"]),
        ("department", ["add_department", "change_department", "view_department"]),
        ("userprofile", ["add_userprofile", "change_userprofile", "view_userprofile"]),
        ("measurement", ["add_measurement", "change_measurement", "view_measurement"]),
        ("alertrule", ["add_alertrule", "change_alertrule", "view_alertrule"]),
        ("alertevent", ["change_alertevent", "view_alertevent"]),
        ("maintenancerequest", ["add_maintenancerequest", "change_maintenancerequest", "view_maintenancerequest"]),
        ("organization", ["view_organization"]),
    ],
    ROLE_OPERADOR: [
        # Operador: registrar consumo, visualizar equipos/zonas y actualizar alertas/mantenimiento
        ("device", ["view_device"]),
        ("measurement", ["add_measurement", "view_measurement"]),
        ("alertevent", ["change_alertevent", "view_alertevent"]),
        ("alertrule", ["view_alertrule"]),
        ("zone", ["view_zone"]),
        ("category", ["view_category"]),
        ("maintenancerequest", ["add_maintenancerequest", "change_maintenancerequest", "view_maintenancerequest"]),
    ],
    ROLE_CONSULTA: [
        # Consulta: solo lectura en los modulos del sistema
        ("device", ["view_device"]),
        ("measurement", ["view_measurement"]),
        ("alertevent", ["view_alertevent"]),
        ("alertrule", ["view_alertrule"]),
        ("zone", ["view_zone"]),
        ("category", ["view_category"]),
        ("organization", ["view_organization"]),
        ("department", ["view_department"]),
        ("maintenancerequest", ["view_maintenancerequest"]),
        ("userprofile", ["view_userprofile"]),
    ],
}


def setup_roles_and_permissions():
    """Crea los grupos de usuarios y les asigna los permisos correspondientes."""
    created_groups = {}
    for role_name, model_specs in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        permissions_to_assign = []
        for model_name, codenames in model_specs:
            perms = Permission.objects.filter(
                content_type__app_label="dispositivos",
                content_type__model=model_name,
                codename__in=codenames,
            )
            permissions_to_assign.extend(list(perms))

        group.permissions.set(permissions_to_assign)
        created_groups[role_name] = group

    return created_groups


def create_demo_users_clase4(default_organization=None):
    """Crea usuarios representativos para cada rol con acceso al Django Admin."""
    User = get_user_model()

    if default_organization is None:
        default_organization, _ = Organization.objects.get_or_create(
            tax_id="76.123.456-7",
            defaults={
                "legal_name": "EcoEnergy Demo SpA",
                "trade_name": "EcoEnergy Demo",
                "contact": "demo@ecoenergy.local",
                "is_active": True,
            },
        )

    dept_ops, _ = Department.objects.get_or_create(
        organization=default_organization,
        name="Operaciones",
        defaults={"description": "Departamento de Operaciones", "is_active": True},
    )

    dept_mon, _ = Department.objects.get_or_create(
        organization=default_organization,
        name="Monitoreo",
        defaults={"description": "Departamento de Monitoreo", "is_active": True},
    )

    setup_roles_and_permissions()

    user_specs = [
        {
            "username": "admin_demo",
            "email": "admin.demo@ecoenergy.local",
            "first_name": "Admin",
            "last_name": "Organizacional",
            "role": ROLE_ADMIN_ORG,
            "department": dept_ops,
            "rut": "11.111.111-1",
            "phone": "+56911112222",
        },
        {
            "username": "operador_demo",
            "email": "operador.demo@ecoenergy.local",
            "first_name": "Carlos",
            "last_name": "Operador",
            "role": ROLE_OPERADOR,
            "department": dept_ops,
            "rut": "22.222.222-2",
            "phone": "+56922223333",
        },
        {
            "username": "consulta_demo",
            "email": "consulta.demo@ecoenergy.local",
            "first_name": "Ana",
            "last_name": "Auditora",
            "role": ROLE_CONSULTA,
            "department": dept_mon,
            "rut": "33.333.333-3",
            "phone": "+56933334444",
        },
    ]

    created_users = []
    default_password = "Password123!"

    for spec in user_specs:
        user, created = User.objects.get_or_create(
            username=spec["username"],
            defaults={
                "email": spec["email"],
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "is_staff": True,
                "is_active": True,
            },
        )
        user.set_password(default_password)
        user.is_staff = True
        user.is_active = True
        user.save()

        # Asignar grupo principal
        group = Group.objects.get(name=spec["role"])
        user.groups.set([group])

        # Crear o actualizar perfil
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "organization": default_organization,
                "department": spec["department"],
                "rut": spec["rut"],
                "phone": spec["phone"],
            },
        )
        created_users.append(user)

    return created_users
