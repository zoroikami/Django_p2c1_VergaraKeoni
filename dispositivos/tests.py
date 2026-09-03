from django.test import TestCase
from django.urls import reverse


class ZonasViewsTest(TestCase):
    def test_listado_zonas_muestra_titulo(self):
        response = self.client.get(reverse('dispositivos:zonas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ZONAS DE CONSUMO')

    def test_detalle_zona_muestra_informacion(self):
        response = self.client.get(reverse('dispositivos:zona_detalle', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detalle de zona')
        self.assertContains(response, 'Zona Norte')

    def test_detalle_zona_inexistente_devuelve_404(self):
        response = self.client.get(reverse('dispositivos:zona_detalle', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_resumen_zonas(self):
        response =self.client.get(reverse('dispositivos:resumen_zonas', args=[999]))
        self.assertEqual(response.status_code, 404)
