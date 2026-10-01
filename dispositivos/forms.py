from django import forms
from .models import Device, Measurement, MaintenanceRequest


class DeviceForm(forms.ModelForm):
    """
    Formulario para la gestión y validación de Dispositivos (Clase 4 y 5).
    Aplica validación de coherencia entre organización y zona.
    """

    class Meta:
        model = Device
        fields = [
            "name",
            "serial_number",
            "organization",
            "category",
            "zone",
            "status",
            "consumption_kwh",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del dispositivo"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: SN-NTE-001"}),
            "organization": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "zone": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "consumption_kwh": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        org = cleaned_data.get("organization")
        zone = cleaned_data.get("zone")
        consumption = cleaned_data.get("consumption_kwh")

        if org and zone and zone.organization_id != org.id:
            self.add_error("zone", "La zona debe pertenecer a la misma organización que el dispositivo.")

        if consumption is not None and consumption < 0:
            self.add_error("consumption_kwh", "El consumo no puede ser negativo.")

        return cleaned_data


class MeasurementForm(forms.ModelForm):
    """Formulario para el registro y auditoría de mediciones de telemetría."""

    class Meta:
        model = Measurement
        fields = ["device", "value_kwh", "unit", "measured_at", "source", "recorded_by", "integration_name"]
        widgets = {
            "device": forms.Select(attrs={"class": "form-select"}),
            "value_kwh": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "measured_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "source": forms.Select(attrs={"class": "form-select"}),
            "recorded_by": forms.Select(attrs={"class": "form-select"}),
            "integration_name": forms.TextInput(attrs={"class": "form-control"}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    """Formulario para la solicitud y control de mantenimiento de dispositivos."""

    class Meta:
        model = MaintenanceRequest
        fields = [
            "device",
            "organization",
            "request_type",
            "reason",
            "priority",
            "status",
            "assigned_to",
            "planned_at",
            "completed_at",
            "result",
            "cost",
        ]
        widgets = {
            "device": forms.Select(attrs={"class": "form-select"}),
            "organization": forms.Select(attrs={"class": "form-select"}),
            "request_type": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "priority": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "planned_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "completed_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "result": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
