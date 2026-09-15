from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Device, Measurement, Organization, UserProfile, Zone

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
