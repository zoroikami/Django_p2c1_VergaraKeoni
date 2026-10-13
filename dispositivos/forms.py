from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import Device, Measurement, MaintenanceRequest, Zone, Category, Organization


class DeviceForm(forms.ModelForm):
    """
    Formulario para la gestión y validación de Dispositivos (Clases 4, 5 y 8).
    Aplica validación de coherencia entre organización y zona, clean_<campo>()
    y scoping de selecciones.
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
        labels = {
            "name": "Nombre del Dispositivo",
            "serial_number": "Número de Serie",
            "organization": "Organización",
            "category": "Categoría",
            "zone": "Zona",
            "status": "Estado",
            "consumption_kwh": "Consumo (kWh)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Medidor Sala Servidores"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: SN-NTE-001"}),
            "organization": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "zone": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "consumption_kwh": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
        }

    def __init__(self, *args, user=None, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Determinar organización por argumento explícito o perfil del usuario
        org = organization
        if not org and user and hasattr(user, "profile") and user.profile:
            org = user.profile.organization

        if org:
            self.fields["organization"].queryset = Organization.objects.filter(pk=org.pk)
            self.fields["organization"].initial = org
            self.fields["organization"].disabled = True
            self.fields["zone"].queryset = Zone.objects.filter(organization=org, deleted_at__isnull=True)
        else:
            self.fields["zone"].queryset = Zone.objects.filter(deleted_at__isnull=True)

        self.fields["category"].queryset = Category.objects.filter(is_active=True, deleted_at__isnull=True)

    def clean_name(self):
        """Validación de longitud mínima y unicidad case-insensitive por organización (Clase 8)."""
        name = self.cleaned_data.get("name", "").strip()
        if len(name) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")

        org = self.cleaned_data.get("organization")
        if not org and self.user and hasattr(self.user, "profile"):
            org = self.user.profile.organization

        if org:
            query = Device.objects.filter(
                organization=org,
                name__iexact=name,
                deleted_at__isnull=True,
            )
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise ValidationError("Ya existe un dispositivo con este nombre en la organización.")

        return name

    def clean_serial_number(self):
        """Validación de número de serie único excluyendo la propia instancia."""
        sn = self.cleaned_data.get("serial_number")
        if sn:
            sn = sn.strip()
            query = Device.objects.filter(serial_number__iexact=sn, deleted_at__isnull=True)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise ValidationError("Ya existe un dispositivo registrado con este número de serie.")
        return sn

    def clean(self):
        cleaned_data = super().clean()
        org = cleaned_data.get("organization")
        if not org and self.user and hasattr(self.user, "profile"):
            org = self.user.profile.organization
            cleaned_data["organization"] = org

        zone = cleaned_data.get("zone")
        consumption = cleaned_data.get("consumption_kwh")

        if org and zone and zone.organization_id != org.id:
            self.add_error("zone", "La zona debe pertenecer a la misma organización que el dispositivo.")

        if consumption is not None and consumption < 0:
            self.add_error("consumption_kwh", "El consumo no puede ser negativo.")

        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Paso 1: Solicitud de código mediante correo electrónico (Clase 6 Desafío)."""
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "nombre@organizacion.cl",
            "autocomplete": "email",
        }),
    )


class PasswordResetVerifyForm(forms.Form):
    """Paso 2: Validación del código temporal de 6 dígitos (Clase 6 Desafío)."""
    code = forms.CharField(
        label="Código de verificación (6 dígitos)",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control text-center fs-3 font-monospace tracking-widest",
            "placeholder": "000000",
            "maxlength": "6",
            "pattern": "[0-9]{6}",
            "autocomplete": "one-time-code",
        }),
    )

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip()
        if not code.isdigit():
            raise ValidationError("El código debe componerse exclusivamente de 6 números.")
        return code


class PasswordResetConfirmForm(forms.Form):
    """Paso 3: Definición y confirmación de la nueva contraseña (Clase 6 Desafío)."""
    new_password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Mínimo 8 caracteres",
            "autocomplete": "new-password",
        }),
    )
    confirm_password = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repite la contraseña",
            "autocomplete": "new-password",
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")

        if p1 and p2:
            if p1 != p2:
                self.add_error("confirm_password", "Las contraseñas ingresadas no coinciden.")
            else:
                password_validation.validate_password(p1, self.user)

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
