from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from core.admin_utils import get_user_organization
from .admin import (
    DepartmentAdmin,
    DeviceAdmin,
    MaintenanceRequestAdmin,
    MeasurementAdmin,
    archive_devices,
)
from .models import (
    Category,
    Department,
    Device,
    MaintenanceRequest,
    Measurement,
    Organization,
    UserProfile,
    Zone,
)
from .roles import (
    ROLE_ADMIN_ORG,
    ROLE_CONSULTA,
    ROLE_OPERADOR,
    create_demo_users_clase4,
    setup_roles_and_permissions,
)

class ZonasViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            legal_name="Organizacion de prueba",
            tax_id="TEST-001",
        )
        cls.category = Category.objects.create(name="Monitoreo")
        cls.zone = Zone.objects.create(
            organization=cls.organization,
            name="Zona Norte",
            limit_kwh=120.50,
        )
        Device.objects.create(
            organization=cls.organization,
            category=cls.category,
            zone=cls.zone,
            name="Medidor de prueba",
            serial_number="TEST-SN-001",
            consumption_kwh=18.40,
        )

    def test_listado_zonas_muestra_titulo(self):
        response = self.client.get(reverse('dispositivos:zonas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ZONAS DE CONSUMO')

    def test_detalle_zona_muestra_informacion(self):
        response = self.client.get(reverse('dispositivos:zona_detalle', args=[self.zone.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detalle de zona')
        self.assertContains(response, 'Zona Norte')

    def test_detalle_zona_inexistente_devuelve_404(self):
        response = self.client.get(reverse('dispositivos:zona_detalle', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_resumen_zonas(self):
        response =self.client.get(reverse('dispositivos:resumen_zonas', args=[999]))
        self.assertEqual(response.status_code, 404)


class DomainRulesTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            legal_name="Organizacion A",
            tax_id="RULE-001",
        )
        self.other_organization = Organization.objects.create(
            legal_name="Organizacion B",
            tax_id="RULE-002",
        )
        self.category = Category.objects.create(name="Reglas")
        self.zone = Zone.objects.create(
            organization=self.organization,
            name="Zona A",
            limit_kwh=100,
        )
        self.other_zone = Zone.objects.create(
            organization=self.other_organization,
            name="Zona B",
            limit_kwh=100,
        )

    def test_device_rejects_zone_from_another_organization(self):
        device = Device(
            organization=self.organization,
            category=self.category,
            zone=self.other_zone,
            name="Equipo cruzado",
            serial_number="RULE-SN-001",
        )
        with self.assertRaises(ValidationError):
            device.full_clean()

    def test_measurement_rejects_negative_values(self):
        device = Device.objects.create(
            organization=self.organization,
            category=self.category,
            zone=self.zone,
            name="Equipo medido",
            serial_number="RULE-SN-002",
        )
        measurement = Measurement(
            device=device,
            value_kwh=-1,
            measured_at="2026-01-01T10:00:00Z",
            source=Measurement.SOURCE_AUTOMATIC,
            integration_name="test",
        )
        with self.assertRaises(ValidationError):
            measurement.full_clean()

    def test_authenticated_user_only_sees_own_organization(self):
        user = get_user_model().objects.create_user(username="operator", password="test-pass")
        UserProfile.objects.create(user=user, organization=self.organization)
        Device.objects.create(
            organization=self.organization,
            category=self.category,
            zone=self.zone,
            name="Equipo visible",
            serial_number="RULE-SN-003",
        )
        Device.objects.create(
            organization=self.other_organization,
            category=self.category,
            zone=self.other_zone,
            name="Equipo oculto",
            serial_number="RULE-SN-004",
        )
        self.client.login(username="operator", password="test-pass")
        response = self.client.get(reverse("dispositivos:catalogo"))
        self.assertContains(response, "Equipo visible")
        self.assertNotContains(response, "Equipo oculto")


class RolesAndPermissionsClase4Test(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(legal_name="Org A", tax_id="ORG-A-001")
        self.org_b = Organization.objects.create(legal_name="Org B", tax_id="ORG-B-002")
        self.dept_a = Department.objects.create(organization=self.org_a, name="Dept A")
        self.dept_b = Department.objects.create(organization=self.org_b, name="Dept B")
        setup_roles_and_permissions()

    def test_user_profile_clean_rejects_foreign_department(self):
        user = get_user_model().objects.create_user(username="test_cross_user")
        profile = UserProfile(
            user=user,
            organization=self.org_a,
            department=self.dept_b,
        )
        with self.assertRaises(ValidationError) as ctx:
            profile.full_clean()
        self.assertIn("department", ctx.exception.message_dict)

    def test_user_profile_clean_accepts_valid_department(self):
        user = get_user_model().objects.create_user(username="test_valid_user")
        profile = UserProfile(
            user=user,
            organization=self.org_a,
            department=self.dept_a,
        )
        profile.full_clean()
        profile.save()
        self.assertEqual(profile.department, self.dept_a)

    def test_roles_and_permissions_matrix(self):
        User = get_user_model()
        users = create_demo_users_clase4(default_organization=self.org_a)
        operador = User.objects.get(username="operador_demo")
        consulta = User.objects.get(username="consulta_demo")
        admin_org = User.objects.get(username="admin_demo")

        # Operador: puede registrar mediciones y ver equipos, pero NO borrar
        self.assertTrue(operador.has_perm("dispositivos.view_device"))
        self.assertTrue(operador.has_perm("dispositivos.add_measurement"))
        self.assertTrue(operador.has_perm("dispositivos.change_alertevent"))
        self.assertFalse(operador.has_perm("dispositivos.delete_device"))
        self.assertFalse(operador.has_perm("dispositivos.delete_measurement"))
        self.assertFalse(operador.has_perm("dispositivos.change_device"))

        # Consulta: solo lectura
        self.assertTrue(consulta.has_perm("dispositivos.view_device"))
        self.assertTrue(consulta.has_perm("dispositivos.view_measurement"))
        self.assertFalse(consulta.has_perm("dispositivos.add_measurement"))
        self.assertFalse(consulta.has_perm("dispositivos.change_measurement"))
        self.assertFalse(consulta.has_perm("dispositivos.delete_device"))

        # Admin Org: gestion operativa amplia, sin borrado fisico
        self.assertTrue(admin_org.has_perm("dispositivos.add_device"))
        self.assertTrue(admin_org.has_perm("dispositivos.change_device"))
        self.assertTrue(admin_org.has_perm("dispositivos.add_measurement"))
        self.assertFalse(admin_org.has_perm("dispositivos.delete_device"))


class AdminSecurityScopingClase5Test(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.device_admin = DeviceAdmin(Device, self.site)
        self.measurement_admin = MeasurementAdmin(Measurement, self.site)
        self.dept_admin = DepartmentAdmin(Department, self.site)
        self.maint_admin = MaintenanceRequestAdmin(MaintenanceRequest, self.site)

        # Dos organizaciones independientes (Norte y Sur)
        self.org_norte = Organization.objects.create(legal_name="EcoEnergy Norte SpA", tax_id="CL5-NTE-01")
        self.org_sur = Organization.objects.create(legal_name="EcoEnergy Sur SpA", tax_id="CL5-SUR-02")

        self.category = Category.objects.create(name="Monitoreo")
        self.zone_norte = Zone.objects.create(organization=self.org_norte, name="Zona Norte")
        self.zone_sur = Zone.objects.create(organization=self.org_sur, name="Zona Sur")

        # Dispositivos Norte (uno activo y uno archivado)
        self.dev_norte_1 = Device.objects.create(
            organization=self.org_norte,
            category=self.category,
            zone=self.zone_norte,
            name="Medidor Norte 1",
            serial_number="CL5-NTE-SN-1",
        )
        self.dev_norte_archived = Device.objects.create(
            organization=self.org_norte,
            category=self.category,
            zone=self.zone_norte,
            name="Medidor Norte Archivado",
            serial_number="CL5-NTE-SN-ARCH",
            deleted_at=timezone.now(),
        )

        # Dispositivo Sur
        self.dev_sur_1 = Device.objects.create(
            organization=self.org_sur,
            category=self.category,
            zone=self.zone_sur,
            name="Medidor Sur 1",
            serial_number="CL5-SUR-SN-1",
        )

        # Usuarios
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="cl5_admin", email="admin@cl5.local", password="pass"
        )
        self.user_norte = User.objects.create_user(
            username="cl5_operador_norte", password="pass", is_staff=True
        )
        UserProfile.objects.create(user=self.user_norte, organization=self.org_norte)

        self.user_sur = User.objects.create_user(
            username="cl5_operador_sur", password="pass", is_staff=True
        )
        UserProfile.objects.create(user=self.user_sur, organization=self.org_sur)

        change_perm = Permission.objects.get(codename="change_device")
        self.user_norte.user_permissions.add(change_perm)
        self.user_sur.user_permissions.add(change_perm)

        self.user_sin_perfil = User.objects.create_user(
            username="cl5_staff_sin_perfil", password="pass", is_staff=True
        )

    def test_get_user_organization_helper(self):
        req_super = self.factory.get("/admin/")
        req_super.user = self.superuser
        self.assertIsNone(get_user_organization(req_super))

        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte
        self.assertEqual(get_user_organization(req_norte), self.org_norte)

        req_sin_perfil = self.factory.get("/admin/")
        req_sin_perfil.user = self.user_sin_perfil
        self.assertIsNone(get_user_organization(req_sin_perfil))

    def test_get_queryset_scopes_to_user_organization_and_excludes_deleted(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte

        qs_norte = self.device_admin.get_queryset(req_norte)
        self.assertIn(self.dev_norte_1, qs_norte)
        self.assertNotIn(self.dev_sur_1, qs_norte)
        self.assertNotIn(self.dev_norte_archived, qs_norte)

        req_sur = self.factory.get("/admin/")
        req_sur.user = self.user_sur
        qs_sur = self.device_admin.get_queryset(req_sur)
        self.assertIn(self.dev_sur_1, qs_sur)
        self.assertNotIn(self.dev_norte_1, qs_sur)

    def test_unassigned_staff_gets_empty_queryset(self):
        req_sin_perfil = self.factory.get("/admin/")
        req_sin_perfil.user = self.user_sin_perfil
        qs = self.device_admin.get_queryset(req_sin_perfil)
        self.assertEqual(qs.count(), 0)

    def test_superuser_sees_all_records_in_queryset(self):
        req_super = self.factory.get("/admin/")
        req_super.user = self.superuser
        qs_super = self.device_admin.get_queryset(req_super)
        self.assertIn(self.dev_norte_1, qs_super)
        self.assertIn(self.dev_sur_1, qs_super)
        self.assertIn(self.dev_norte_archived, qs_super)

    def test_formfield_for_foreignkey_limits_devices_to_user_organization(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte

        db_field = Measurement._meta.get_field("device")
        formfield = self.measurement_admin.formfield_for_foreignkey(db_field, req_norte)
        queryset = formfield.queryset

        self.assertIn(self.dev_norte_1, queryset)
        self.assertNotIn(self.dev_sur_1, queryset)
        self.assertNotIn(self.dev_norte_archived, queryset)

    def test_save_model_auto_assigns_organization(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte

        new_device = Device(
            name="Nuevo Medidor",
            serial_number="NEW-SN-999",
            category=self.category,
            zone=self.zone_norte,
        )
        self.device_admin.save_model(req_norte, new_device, None, change=False)
        self.assertEqual(new_device.organization, self.org_norte)

    def test_has_change_permission_restricts_object_to_own_organization(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte

        # Dispositivo de su organizacion -> permitido
        self.assertTrue(self.device_admin.has_change_permission(req_norte, self.dev_norte_1))
        # Dispositivo de otra organizacion -> denegado
        self.assertFalse(self.device_admin.has_change_permission(req_norte, self.dev_sur_1))

    def test_has_delete_permission_is_disabled(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte
        self.assertFalse(self.device_admin.has_delete_permission(req_norte, self.dev_norte_1))

    def test_archive_devices_action(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        active_dev = Device.objects.create(
            organization=self.org_norte,
            category=self.category,
            zone=self.zone_norte,
            name="Para archivar",
            serial_number="SN-ARCH-TEST",
        )
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte
        setattr(req_norte, "session", {})
        setattr(req_norte, "_messages", FallbackStorage(req_norte))

        archive_devices(self.device_admin, req_norte, Device.objects.filter(pk=active_dev.pk))
        active_dev.refresh_from_db()
        self.assertIsNotNone(active_dev.deleted_at)

    def test_has_view_permission_restricts_object_to_own_organization(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte

        self.assertTrue(self.device_admin.has_view_permission(req_norte, self.dev_norte_1))
        self.assertFalse(self.device_admin.has_view_permission(req_norte, self.dev_sur_1))

    def test_formfield_for_foreignkey_department_and_maintenance(self):
        req_norte = self.factory.get("/admin/")
        req_norte.user = self.user_norte

        # Selector de equipos en mantenimiento limitado a la organizacion del usuario
        db_field_device = MaintenanceRequest._meta.get_field("device")
        field_device = self.maint_admin.formfield_for_foreignkey(db_field_device, req_norte)
        self.assertIn(self.dev_norte_1, field_device.queryset)
        self.assertNotIn(self.dev_sur_1, field_device.queryset)

        # Selector de usuario asignado en mantenimiento limitado a la organizacion del usuario
        db_field_assigned = MaintenanceRequest._meta.get_field("assigned_to")
        field_assigned = self.maint_admin.formfield_for_foreignkey(db_field_assigned, req_norte)
        self.assertIn(self.user_norte, field_assigned.queryset)
        self.assertNotIn(self.user_sur, field_assigned.queryset)

    def test_defense_question_operador_norte_cannot_interact_with_sur(self):
        # Otorgar permisos operativos reales al usuario operador
        view_device = Permission.objects.get(codename="view_device")
        add_meas = Permission.objects.get(codename="add_measurement")
        view_meas = Permission.objects.get(codename="view_measurement")
        self.user_norte.user_permissions.add(view_device, add_meas, view_meas)

        self.client.force_login(self.user_norte)

        # 1. Changelist de dispositivos en Django Admin: solo ve los de EcoEnergy Norte
        response = self.client.get(reverse("admin:dispositivos_device_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dev_norte_1.name)
        self.assertNotContains(response, self.dev_sur_1.name)

        # 2. Intento de acceso directo por manipulacion de ID en URL a dispositivo de Sur:
        # Django Admin bloquea el acceso (redireccion segura con codigo 302 hacia /admin/ o changelist, o 403/404)
        response_sur = self.client.get(
            reverse("admin:dispositivos_device_change", args=[self.dev_sur_1.pk])
        )
        self.assertIn(response_sur.status_code, [302, 403, 404])
        if response_sur.status_code == 302:
            self.assertIn(response_sur.url, [reverse("admin:index"), reverse("admin:dispositivos_device_changelist")])

        # Verificacion con follow=True: nunca se renderiza la informacion del equipo de Sur
        response_followed = self.client.get(
            reverse("admin:dispositivos_device_change", args=[self.dev_sur_1.pk]),
            follow=True,
        )
        self.assertNotContains(response_followed, self.dev_sur_1.name)

        # 3. Formulario de medicion: en el selector de device NO aparece el de Sur
        response_add_meas = self.client.get(reverse("admin:dispositivos_measurement_add"))
        self.assertEqual(response_add_meas.status_code, 200)
        self.assertContains(response_add_meas, self.dev_norte_1.name)
        self.assertNotContains(response_add_meas, self.dev_sur_1.name)
