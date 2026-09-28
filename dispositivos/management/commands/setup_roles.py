from django.core.management.base import BaseCommand

from dispositivos.roles import create_demo_users_clase4, setup_roles_and_permissions


class Command(BaseCommand):
    help = "Configura los grupos, matriz de permisos y usuarios de demostracion de la Clase 4."

    def handle(self, *args, **options):
        self.stdout.write("Configurando grupos y permisos de EcoEnergy...")
        groups = setup_roles_and_permissions()
        for name, group in groups.items():
            perm_count = group.permissions.count()
            self.stdout.write(f" - Grupo '{name}': {perm_count} permisos asignados.")

        self.stdout.write("Creando usuarios de prueba para cada rol...")
        users = create_demo_users_clase4()
        for user in users:
            roles = ", ".join(user.groups.values_list("name", flat=True))
            profile = getattr(user, "profile", None)
            org_name = profile.organization.legal_name if profile else "Sin org"
            self.stdout.write(
                f" - Usuario '{user.username}' (clave: Password123!) | Rol: [{roles}] | Org: {org_name}"
            )

        self.stdout.write(self.style.SUCCESS("Roles, permisos y usuarios configurados exitosamente."))
