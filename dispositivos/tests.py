from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
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
    archive_selected_records,
)
from .models import (
    Category,
    Department,
    Device,
    MaintenanceRequest,
    Measurement,
    Organization,
    PasswordResetCode,
    UserProfile,
    Zone,
)
from datetime import timedelta
from django.core import mail
from django.contrib.auth.hashers import make_password
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
        perm = Permission.objects.filter(codename="view_device").first()
        if perm:
            user.user_permissions.add(perm)
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

    def test_organization_admin_allows_own_inline_department_edit(self):
        setup_roles_and_permissions()
        self.user_norte.groups.add(Group.objects.get(name=ROLE_ADMIN_ORG))
        self.client.force_login(self.user_norte)
        url = reverse("admin:dispositivos_organization_change", args=[self.org_norte.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="departments-TOTAL_FORMS"')
        self.assertContains(response, 'name="departments-__prefix__-name"')

        response = self.client.post(url, {
            "legal_name": self.org_norte.legal_name,
            "tax_id": self.org_norte.tax_id,
            "trade_name": "EcoEnergy Norte",
            "contact": "contacto@norte.example",
            "is_active": "on",
            "departments-TOTAL_FORMS": "1",
            "departments-INITIAL_FORMS": "0",
            "departments-MIN_NUM_FORMS": "0",
            "departments-MAX_NUM_FORMS": "1000",
            "departments-0-name": "Nuevo departamento Norte",
            "departments-0-is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(
            organization=self.org_norte, name="Nuevo departamento Norte"
        ).exists())

        foreign_response = self.client.get(reverse(
            "admin:dispositivos_organization_change", args=[self.org_sur.pk]
        ))
        self.assertIn(foreign_response.status_code, (302, 403, 404))

    def test_device_admin_shows_zone_validation_on_field(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("admin:dispositivos_device_add"),
            {
                "name": "Equipo cruzado",
                "organization": self.org_norte.pk,
                "category": self.category.pk,
                "zone": self.zone_sur.pk,
                "status": Device.STATUS_ACTIVE,
                "consumption_kwh": "10.00",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("zone", response.context["adminform"].form.errors)
        self.assertContains(response, "La zona debe pertenecer a la misma organización")

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
        self.assertTrue(Device.objects.filter(pk=active_dev.pk).exists())
        self.assertIn("1 dispositivo(s) archivado(s)", str(list(req_norte._messages)[0]))

    def test_generic_archive_action_keeps_department_record(self):
        from django.contrib.messages.storage.fallback import FallbackStorage

        department = Department.objects.create(
            organization=self.org_norte, name="Departamento para archivar"
        )
        request = self.factory.post("/admin/dispositivos/department/")
        request.user = self.user_norte
        request.session = {}
        request._messages = FallbackStorage(request)

        archive_selected_records(
            self.dept_admin, request, Department.objects.filter(pk=department.pk)
        )
        department.refresh_from_db()
        self.assertIsNotNone(department.deleted_at)
        self.assertTrue(Department.objects.filter(pk=department.pk).exists())
        self.assertIn("1 registro(s) archivado(s) exitosamente", str(list(request._messages)[0]))


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


class SeedDataReproducibilityTest(TestCase):
    def test_seed_is_repeatable_and_includes_an_archived_device(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Organization.objects.filter(
            legal_name__in=["EcoEnergy Norte SpA", "EcoEnergy Sur SpA"]
        ).count(), 2)
        self.assertTrue(Device.objects.filter(
            serial_number="SN-NTE-ARCH-001", deleted_at__isnull=False
        ).exists())
        self.assertEqual(Measurement.objects.count(), 8)
        for username in (
            "admin", "admin_norte", "operador_norte", "consulta_norte",
            "operador_sur", "staff_sin_perfil",
        ):
            self.assertTrue(get_user_model().objects.filter(username=username).exists())

        Device.objects.filter(serial_number="SN-NTE-001").update(deleted_at=timezone.now())
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Measurement.objects.count(), 8)
        self.assertEqual(Device.objects.filter(serial_number="SN-NTE-ARCH-001").count(), 1)
        self.assertIsNone(Device.objects.get(serial_number="SN-NTE-001").deleted_at)


# ==============================================================================
# PRUEBAS CLASE 6: Autenticación, Sesiones y Mensajes
# ==============================================================================

class Clase6AuthAndSessionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_data", stdout=StringIO())
        cls.User = get_user_model()
        cls.user = cls.User.objects.get(username="admin_norte")

    def test_login_page_renders_with_csrf(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingreso al Sistema")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_valid_credentials_redirects(self):
        response = self.client.post(
            reverse("login"),
            {"username": "admin_norte", "password": "Password123!"},
        )
        self.assertRedirects(response, reverse("dispositivos:catalogo"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_invalid_credentials_shows_controlled_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": "admin_norte", "password": "ClaveIncorrecta!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuario o contraseña incorrectos.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_user_redirected_from_protected_view(self):
        response = self.client.get(reverse("dispositivos:catalogo"))
        expected_url = f"{reverse('login')}?next={reverse('dispositivos:catalogo')}"
        self.assertRedirects(response, expected_url)

    def test_session_tracks_visits(self):
        res1 = self.client.get(reverse("dispositivos:inicio"))
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(self.client.session.get("inicio_visits"), 1)

        res2 = self.client.get(reverse("dispositivos:inicio"))
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(self.client.session.get("inicio_visits"), 2)

    def test_logout_post_invalidates_session(self):
        self.client.login(username="operador_norte", password="Password123!")
        res_cat = self.client.get(reverse("dispositivos:catalogo"))
        self.assertEqual(res_cat.status_code, 200)

        # Logout via POST
        res_logout = self.client.post(reverse("logout"))
        self.assertRedirects(res_logout, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

        # Volver a URL protegida redirige a login
        res_after = self.client.get(reverse("dispositivos:catalogo"))
        self.assertEqual(res_after.status_code, 302)


# ==============================================================================
# PRUEBAS CLASE 6 DESAFÍO: Recuperación de Contraseña con Código Temporal
# ==============================================================================

class Clase6PasswordResetTemporalCodeTest(TestCase):
    def setUp(self):
        call_command("seed_data", stdout=StringIO())
        self.User = get_user_model()
        self.user = self.User.objects.get(username="operador_norte")
        self.email = self.user.email
        mail.outbox.clear()

    def test_caso1_codigo_correcto_antes_de_120s_permite_continuar(self):
        # Solicitar código
        res_req = self.client.post(
            reverse("dispositivos:password_reset_request"),
            {"email": self.email},
        )
        self.assertRedirects(res_req, reverse("dispositivos:password_reset_verify"))
        self.assertEqual(len(mail.outbox), 1)

        code_obj = PasswordResetCode.objects.filter(user=self.user, is_used=False).first()
        self.assertIsNotNone(code_obj)
        self.assertFalse(code_obj.is_expired())

        # Forzar un código conocido para verificar
        code_obj.code_hash = make_password("654321")
        code_obj.save()

        # Validar código
        res_verify = self.client.post(
            reverse("dispositivos:password_reset_verify"),
            {"code": "654321"},
        )
        self.assertRedirects(res_verify, reverse("dispositivos:password_reset_confirm"))

    def test_caso2_codigo_incorrecto_incrementa_intentos_y_rechaza(self):
        self.client.post(
            reverse("dispositivos:password_reset_request"),
            {"email": self.email},
        )
        code_obj = PasswordResetCode.objects.filter(user=self.user, is_used=False).first()
        code_obj.code_hash = make_password("111222")
        code_obj.save()

        res_wrong = self.client.post(
            reverse("dispositivos:password_reset_verify"),
            {"code": "999999"},
        )
        self.assertEqual(res_wrong.status_code, 200)
        self.assertContains(res_wrong, "Código incorrecto")
        code_obj.refresh_from_db()
        self.assertEqual(code_obj.failed_attempts, 1)

    def test_caso3_codigo_despues_de_120s_rechaza_por_expiracion(self):
        self.client.post(
            reverse("dispositivos:password_reset_request"),
            {"email": self.email},
        )
        code_obj = PasswordResetCode.objects.filter(user=self.user, is_used=False).first()
        code_obj.code_hash = make_password("123456")
        code_obj.expires_at = timezone.now() - timedelta(seconds=10)
        code_obj.save()

        res_expired = self.client.post(
            reverse("dispositivos:password_reset_verify"),
            {"code": "123456"},
        )
        self.assertEqual(res_expired.status_code, 200)
        self.assertContains(res_expired, "El código ha expirado")

    def test_caso4_codigo_ya_utilizado_no_permite_reutilizar(self):
        self.client.post(
            reverse("dispositivos:password_reset_request"),
            {"email": self.email},
        )
        code_obj = PasswordResetCode.objects.filter(user=self.user, is_used=False).first()
        code_obj.code_hash = make_password("123456")
        code_obj.is_used = True
        code_obj.save()

        res_used = self.client.post(
            reverse("dispositivos:password_reset_verify"),
            {"code": "123456"},
        )
        self.assertEqual(res_used.status_code, 200)
        self.assertContains(res_used, "No existe una solicitud de recuperación vigente")

    def test_caso5_solicitud_nuevo_codigo_invalida_anterior(self):
        # Primera solicitud
        self.client.post(reverse("dispositivos:password_reset_request"), {"email": self.email})
        code1 = PasswordResetCode.objects.filter(user=self.user).latest("created_at")

        # Segunda solicitud
        self.client.post(reverse("dispositivos:password_reset_request"), {"email": self.email})
        code1.refresh_from_db()
        self.assertTrue(code1.is_used)

        code2 = PasswordResetCode.objects.filter(user=self.user).latest("created_at")
        self.assertNotEqual(code1.pk, code2.pk)
        self.assertFalse(code2.is_used)

    def test_caso6_correo_inexistente_respuesta_generica(self):
        res = self.client.post(
            reverse("dispositivos:password_reset_request"),
            {"email": "no_existe_en_bd@ejemplo.com"},
        )
        self.assertRedirects(res, reverse("dispositivos:password_reset_verify"))
        self.assertEqual(len(mail.outbox), 0)

    def test_caso7_nueva_contrasena_correcta_actualiza_y_permite_login(self):
        # 1. Request
        self.client.post(reverse("dispositivos:password_reset_request"), {"email": self.email})
        code_obj = PasswordResetCode.objects.filter(user=self.user, is_used=False).first()
        code_obj.code_hash = make_password("789123")
        code_obj.save()

        # 2. Verify
        self.client.post(reverse("dispositivos:password_reset_verify"), {"code": "789123"})

        # 3. Confirm
        nueva_clave = "NuevaSuperClave2026!"
        res_confirm = self.client.post(
            reverse("dispositivos:password_reset_confirm"),
            {
                "new_password": nueva_clave,
                "confirm_password": nueva_clave,
            },
        )
        self.assertRedirects(res_confirm, reverse("login"))

        code_obj.refresh_from_db()
        self.assertTrue(code_obj.is_used)
        self.assertIsNotNone(code_obj.used_at)

        # 4. Probar login con nueva clave
        res_login_nuevo = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": nueva_clave},
        )
        self.assertRedirects(res_login_nuevo, reverse("dispositivos:catalogo"))

        # 5. Probar que clave antigua ya no funciona
        self.client.logout()
        res_login_viejo = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "Password123!"},
        )
        self.assertEqual(res_login_viejo.status_code, 200)
        self.assertContains(res_login_viejo, "Usuario o contraseña incorrectos.")


# ==============================================================================
# PRUEBAS CLASE 7: Permisos en Vistas, Grupos, Scoping y Error 403
# ==============================================================================

class Clase7PermissionsAndScopingViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_data", stdout=StringIO())
        cls.User = get_user_model()
        cls.admin_norte = cls.User.objects.get(username="admin_norte")
        cls.operador_norte = cls.User.objects.get(username="operador_norte")
        cls.consulta_norte = cls.User.objects.get(username="consulta_norte")
        cls.dev_norte = Device.objects.filter(organization__trade_name="EcoEnergy Norte").first()
        cls.dev_sur = Device.objects.filter(organization__trade_name="EcoEnergy Sur").first()

    def test_consulta_can_view_device_list(self):
        self.client.login(username="consulta_norte", password="Password123!")
        res = self.client.get(reverse("dispositivos:catalogo"))
        self.assertEqual(res.status_code, 200)

    def test_consulta_denied_403_on_create_device(self):
        self.client.login(username="consulta_norte", password="Password123!")
        res = self.client.get(reverse("dispositivos:device_create"))
        self.assertEqual(res.status_code, 403)
        self.assertTemplateUsed(res, "403.html")

    def test_consulta_denied_403_on_update_device(self):
        self.client.login(username="consulta_norte", password="Password123!")
        res = self.client.get(reverse("dispositivos:device_update", args=[self.dev_norte.pk]))
        self.assertEqual(res.status_code, 403)
        self.assertTemplateUsed(res, "403.html")

    def test_user_without_delete_perm_denied_403_on_delete(self):
        # admin_norte posee add y change, pero no delete
        self.client.login(username="admin_norte", password="Password123!")
        res = self.client.post(reverse("dispositivos:device_delete", args=[self.dev_norte.pk]))
        self.assertEqual(res.status_code, 403)
        self.assertTemplateUsed(res, "403.html")

    def test_scoping_cross_organization_returns_404(self):
        # admin_norte tiene change_device, pero no puede acceder a un dispositivo de EcoEnergy Sur
        self.client.login(username="admin_norte", password="Password123!")
        res = self.client.get(reverse("dispositivos:device_update", args=[self.dev_sur.pk]))
        self.assertEqual(res.status_code, 404)


# ==============================================================================
# PRUEBAS CLASE 8: CRUD Completo Protegido, ModelForm, Modal y SweetAlert2
# ==============================================================================

class Clase8ProtectedCrudModelFormAndSwalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_data", stdout=StringIO())
        cls.User = get_user_model()
        cls.admin_norte = cls.User.objects.get(username="admin_norte")
        cls.org_norte = Organization.objects.get(trade_name="EcoEnergy Norte")
        cls.zone_norte = Zone.objects.filter(organization=cls.org_norte).first()
        cls.cat = Category.objects.first()

    def test_list_view_scoped_to_organization(self):
        self.client.login(username="admin_norte", password="Password123!")
        res = self.client.get(reverse("dispositivos:catalogo"))
        self.assertEqual(res.status_code, 200)
        # Todos los dispositivos en el contexto deben pertenecer a EcoEnergy Norte
        for dev in res.context["dispositivos"]:
            self.assertEqual(dev.organization_id, self.org_norte.pk)

    def test_create_view_valid_form(self):
        self.client.login(username="admin_norte", password="Password123!")
        payload = {
            "name": "Sensor Clima Servidores Norte",
            "serial_number": "SN-NTE-NEW-888",
            "organization": self.org_norte.pk,
            "category": self.cat.pk,
            "zone": self.zone_norte.pk,
            "status": "active",
            "consumption_kwh": "18.50",
        }
        res = self.client.post(reverse("dispositivos:device_create"), payload)
        self.assertRedirects(res, reverse("dispositivos:catalogo"))

        dev = Device.objects.get(serial_number="SN-NTE-NEW-888")
        self.assertEqual(dev.organization, self.org_norte)
        self.assertEqual(dev.name, "Sensor Clima Servidores Norte")

    def test_create_view_invalid_form_reopens_modal(self):
        self.client.login(username="admin_norte", password="Password123!")
        # Nombre menor a 3 caracteres viola clean_name()
        payload = {
            "name": "AB",
            "serial_number": "SN-FAIL-001",
            "category": self.cat.pk,
            "zone": self.zone_norte.pk,
            "status": "active",
            "consumption_kwh": "10.00",
        }
        res = self.client.post(reverse("dispositivos:device_create"), payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context.get("open_modal"))
        self.assertFormError(res.context["form"], "name", "El nombre debe tener al menos 3 caracteres.")

    def test_clean_name_duplicate_rejected(self):
        self.client.login(username="admin_norte", password="Password123!")
        existing_name = Device.objects.filter(organization=self.org_norte).first().name
        payload = {
            "name": existing_name.lower(),  # Comprobar unicidad case-insensitive
            "serial_number": "SN-DUP-001",
            "category": self.cat.pk,
            "zone": self.zone_norte.pk,
            "status": "active",
            "consumption_kwh": "10.00",
        }
        res = self.client.post(reverse("dispositivos:device_create"), payload)
        self.assertEqual(res.status_code, 200)
        self.assertFormError(res.context["form"], "name", "Ya existe un dispositivo con este nombre en la organización.")

    def test_update_view_valid(self):
        self.client.login(username="admin_norte", password="Password123!")
        dev = Device.objects.filter(organization=self.org_norte).first()
        payload = {
            "name": "Medidor Principal Norte Renombrado",
            "serial_number": dev.serial_number,
            "organization": self.org_norte.pk,
            "category": dev.category_id,
            "zone": dev.zone_id,
            "status": "active",
            "consumption_kwh": "25.00",
        }
        res = self.client.post(reverse("dispositivos:device_update", args=[dev.pk]), payload)
        self.assertRedirects(res, reverse("dispositivos:catalogo"))

        dev.refresh_from_db()
        self.assertEqual(dev.name, "Medidor Principal Norte Renombrado")

    def test_delete_view_soft_delete(self):
        # Superusuario posee todos los permisos, incluyendo delete_device
        self.client.login(username="admin", password="Admin123!")
        dev = Device.objects.filter(organization=self.org_norte, deleted_at__isnull=True).first()
        dev_pk = dev.pk

        res = self.client.post(reverse("dispositivos:device_delete", args=[dev_pk]))
        self.assertRedirects(res, reverse("dispositivos:catalogo"))

        # Borrado lógico: sigue en la base de datos con deleted_at asignado
        dev.refresh_from_db()
        self.assertIsNotNone(dev.deleted_at)

        # Ya no debe aparecer en el listado activo
        res_list = self.client.get(reverse("dispositivos:catalogo"))
        pks_in_list = [d.pk for d in res_list.context["dispositivos"]]
        self.assertNotIn(dev_pk, pks_in_list)
