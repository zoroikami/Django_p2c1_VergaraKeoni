from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class BaseModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	deleted_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		abstract = True


class Category(BaseModel):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ("name",)
		verbose_name = "categoría"
		verbose_name_plural = "categorías"

	def __str__(self):
		return self.name


class Zone(BaseModel):
	organization = models.ForeignKey(
		"Organization",
		on_delete=models.PROTECT,
		related_name="zones",
	)
	name = models.CharField(max_length=100)
	limit_kwh = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ("organization__legal_name", "name")
		verbose_name = "zona"
		verbose_name_plural = "zonas"
		constraints = [
			models.UniqueConstraint(
				fields=("organization", "name"),
				name="unique_zone_name_per_organization",
			)
		]

	def __str__(self):
		return self.name


class Device(BaseModel):
	STATUS_ACTIVE = "active"
	STATUS_MAINTENANCE = "maintenance"
	STATUS_RETIRED = "retired"
	STATUS_CHOICES = (
		(STATUS_ACTIVE, "Active"),
		(STATUS_MAINTENANCE, "Maintenance"),
		(STATUS_RETIRED, "Retired"),
	)

	name = models.CharField(max_length=120)
	organization = models.ForeignKey(
		"Organization",
		on_delete=models.PROTECT,
		related_name="devices",
	)
	serial_number = models.CharField(max_length=80, unique=True, null=True, blank=True)
	category = models.ForeignKey(
		Category,
		on_delete=models.PROTECT,
		related_name="devices",
	)
	zone = models.ForeignKey(
		Zone,
		on_delete=models.PROTECT,
		related_name="devices",
	)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
	consumption_kwh = models.DecimalField(max_digits=10, decimal_places=2, default=0)

	class Meta:
		ordering = ("name",)
		verbose_name = "dispositivo"
		verbose_name_plural = "dispositivos"
		indexes = [models.Index(fields=("organization", "status"))]

	def __str__(self):
		identity = self.serial_number or f"ID {self.pk}"
		return f"{self.name} · {identity}"

	def clean(self):
		if self.zone_id and self.organization_id and self.zone.organization_id != self.organization_id:
			raise ValidationError({
				"zone": "La zona debe pertenecer a la misma organización que el dispositivo."
			})
		if self.consumption_kwh is not None and self.consumption_kwh < 0:
			raise ValidationError({"consumption_kwh": "El consumo no puede ser negativo."})
		if self.status == self.STATUS_RETIRED:
			return


class Organization(BaseModel):
	legal_name = models.CharField(max_length=150)
	tax_id = models.CharField(max_length=20, unique=True)
	trade_name = models.CharField(max_length=150, blank=True)
	contact = models.CharField(max_length=150, blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ("legal_name",)
		verbose_name = "organización"
		verbose_name_plural = "organizaciones"

	def __str__(self):
		return self.trade_name or self.legal_name


class Department(BaseModel):
	organization = models.ForeignKey(
		Organization,
		on_delete=models.PROTECT,
		related_name="departments",
	)
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	manager = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="managed_departments",
	)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ("organization__legal_name", "name")
		verbose_name = "departamento"
		verbose_name_plural = "departamentos"
		constraints = [
			models.UniqueConstraint(
				fields=("organization", "name"),
				name="unique_department_name_per_organization",
			)
		]

	def __str__(self):
		return f"{self.organization} · {self.name}"

	def clean(self):
		if self.manager_id:
			profile = getattr(self.manager, "profile", None)
			if not profile or profile.organization_id != self.organization_id or not self.manager.is_active:
				raise ValidationError("The manager must be an active user in the same organization.")


class UserProfile(BaseModel):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="profile",
	)
	organization = models.ForeignKey(
		Organization,
		on_delete=models.PROTECT,
		related_name="user_profiles",
	)
	department = models.ForeignKey(
		Department,
		on_delete=models.PROTECT,
		related_name="user_profiles",
		null=True,
		blank=True,
	)
	rut = models.CharField(max_length=20, blank=True)
	phone = models.CharField(max_length=30, blank=True)
	address = models.CharField(max_length=200, blank=True)

	class Meta:
		verbose_name = "perfil de usuario"
		verbose_name_plural = "perfiles de usuario"

	def __str__(self):
		return f"{self.user.get_full_name() or self.user.username} · {self.organization}"

	def clean(self):
		super().clean()
		if self.department_id and self.department.organization_id != self.organization_id:
			raise ValidationError({
				"department": "El departamento debe pertenecer a la organización seleccionada."
			})


class Measurement(BaseModel):
	SOURCE_MANUAL = "manual"
	SOURCE_AUTOMATIC = "automatic"
	SOURCE_CHOICES = (
		(SOURCE_MANUAL, "Manual"),
		(SOURCE_AUTOMATIC, "Automatic"),
	)

	device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="measurements")
	value_kwh = models.DecimalField(max_digits=12, decimal_places=3)
	unit = models.CharField(max_length=20, default="kWh")
	measured_at = models.DateTimeField()
	source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
	recorded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="recorded_measurements",
	)
	integration_name = models.CharField(max_length=120, blank=True)
	deleted_reason = models.TextField(blank=True)

	class Meta:
		ordering = ("-measured_at",)
		verbose_name = "medición"
		verbose_name_plural = "mediciones"
		indexes = [models.Index(fields=("device", "measured_at"))]

	def __str__(self):
		return f"{self.device} · {self.measured_at:%Y-%m-%d %H:%M}"

	def clean(self):
		if self.value_kwh < 0:
			raise ValidationError("Measurement value cannot be negative.")
		if self.source == self.SOURCE_MANUAL and not self.recorded_by_id:
			raise ValidationError("Manual measurements require the recording user.")
		if self.source == self.SOURCE_AUTOMATIC and not self.integration_name:
			raise ValidationError("Automatic measurements require an integration source.")
		if self.device_id and self.device.status == Device.STATUS_RETIRED:
			raise ValidationError("Retired devices cannot receive new measurements.")


class AlertRule(BaseModel):
	name = models.CharField(max_length=120)
	severity = models.CharField(max_length=30)
	unit = models.CharField(max_length=20, default="kWh")
	minimum = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
	maximum = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="alert_rules")
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ("name",)
		verbose_name = "regla de alerta"
		verbose_name_plural = "reglas de alerta"

	def __str__(self):
		return self.name

	def clean(self):
		if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
			raise ValidationError("The minimum limit cannot exceed the maximum limit.")


class AlertEvent(BaseModel):
	STATUS_OPEN = "open"
	STATUS_ACKNOWLEDGED = "acknowledged"
	STATUS_RESOLVED = "resolved"
	STATUS_CHOICES = (
		(STATUS_OPEN, "Open"),
		(STATUS_ACKNOWLEDGED, "Acknowledged"),
		(STATUS_RESOLVED, "Resolved"),
	)

	measurement = models.ForeignKey(Measurement, on_delete=models.PROTECT, related_name="alert_events")
	device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="alert_events")
	rule = models.ForeignKey(AlertRule, on_delete=models.PROTECT, related_name="events")
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
	effective_minimum = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
	effective_maximum = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
	resolved_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="resolved_alerts",
	)
	resolved_at = models.DateTimeField(null=True, blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		verbose_name = "evento de alerta"
		verbose_name_plural = "eventos de alerta"

	def __str__(self):
		return f"{self.device} · {self.get_status_display()}"


class MaintenanceRequest(BaseModel):
	PREVENTIVE = "preventive"
	CORRECTIVE = "corrective"
	TYPE_CHOICES = ((PREVENTIVE, "Preventive"), (CORRECTIVE, "Corrective"))
	OPEN = "open"
	IN_PROGRESS = "in_progress"
	CLOSED = "closed"
	STATUS_CHOICES = ((OPEN, "Open"), (IN_PROGRESS, "In progress"), (CLOSED, "Closed"))

	device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="maintenance_requests")
	organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="maintenance_requests")
	request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
	reason = models.TextField()
	priority = models.CharField(max_length=20, default="normal")
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
	assigned_to = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="assigned_maintenance",
	)
	planned_at = models.DateTimeField(null=True, blank=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	diagnosis = models.TextField(blank=True)
	actions_taken = models.TextField(blank=True)
	result = models.TextField(blank=True)
	cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

	class Meta:
		verbose_name = "solicitud de mantenimiento"
		verbose_name_plural = "solicitudes de mantenimiento"

	def __str__(self):
		return f"{self.device} · {self.get_request_type_display()}"

	def clean(self):
		if self.device_id and self.organization_id and self.device.organization_id != self.organization_id:
			raise ValidationError("The maintenance organization must match the device organization.")
		if self.status == self.CLOSED and (not self.completed_at or not self.result):
			raise ValidationError("Closed maintenance requires completion date and result.")
