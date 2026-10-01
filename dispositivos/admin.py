from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.admin_utils import get_user_organization
from .models import (
	AlertEvent,
	AlertRule,
	Category,
	Department,
	Device,
	MaintenanceRequest,
	Measurement,
	Organization,
	UserProfile,
	Zone,
)


def check_scoped_object_permission(user, obj):
	"""Comprueba si un objeto pertenece al ámbito organizacional del usuario."""
	if obj is None or user.is_superuser:
		return True
	profile = getattr(user, "profile", None)
	if not profile or not profile.organization_id:
		return False
	user_org_id = profile.organization_id

	if hasattr(obj, "organization_id") and obj.organization_id is not None:
		return obj.organization_id == user_org_id
	if getattr(obj, "device_id", None) is not None:
		return obj.device.organization_id == user_org_id
	if isinstance(obj, Organization):
		return obj.id == user_org_id
	return True


@admin.action(
	description="Archivar dispositivos seleccionados",
	permissions=["change"],
)
def archive_devices(modeladmin, request, queryset):
	"""Accion personalizada para borrado logico de dispositivos (Clase 5)."""
	updated = queryset.filter(deleted_at__isnull=True).update(deleted_at=timezone.now())
	modeladmin.message_user(
		request,
		f"{updated} dispositivo(s) archivado(s).",
		level=messages.SUCCESS,
	)


@admin.action(
	description="Archivar registros seleccionados (borrado logico)",
	permissions=["change"],
)
def archive_selected_records(modeladmin, request, queryset):
	"""Accion generica para borrado logico de registros con BaseModel (Clase 5)."""
	updated = queryset.filter(deleted_at__isnull=True).update(deleted_at=timezone.now())
	modeladmin.message_user(
		request,
		f"{updated} registro(s) archivado(s) exitosamente.",
		level=messages.SUCCESS,
	)


class DepartmentInline(admin.TabularInline):
	"""Inline para gestionar departamentos desde una organizacion (Clase 5, Slide 15)."""
	model = Department
	extra = 0
	fields = ("name", "manager", "is_active")
	show_change_link = True

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == "manager" and not request.user.is_superuser:
			org = get_user_organization(request)
			if org:
				kwargs["queryset"] = get_user_model().objects.filter(
					profile__organization=org, is_active=True
				)
			else:
				kwargs["queryset"] = get_user_model().objects.none()
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def has_delete_permission(self, request, obj=None):
		return False


class AuditedAdmin(admin.ModelAdmin):
	readonly_fields = ("created_at", "updated_at", "deleted_at")


@admin.register(Organization)
class OrganizationAdmin(AuditedAdmin):
	list_display = ("tax_id", "legal_name", "trade_name", "is_active")
	search_fields = ("legal_name", "tax_id", "trade_name")
	list_filter = ("is_active",)
	ordering = ("legal_name",)
	inlines = [DepartmentInline]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		org = get_user_organization(request)
		if not org:
			return qs.none()
		return qs.filter(pk=org.pk, deleted_at__isnull=True)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(Department)
class DepartmentAdmin(AuditedAdmin):
	list_display = ("name", "organization", "manager", "is_active")
	search_fields = ("name", "organization__legal_name", "manager__username")
	list_filter = ("organization", "is_active")
	list_select_related = ("organization", "manager")
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		org = get_user_organization(request)
		if not org:
			return qs.none()
		return qs.filter(organization=org, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			org = get_user_organization(request)
			if db_field.name == "organization":
				kwargs["queryset"] = Organization.objects.filter(pk=org.pk) if org else Organization.objects.none()
			elif db_field.name == "manager":
				kwargs["queryset"] = (
					get_user_model().objects.filter(profile__organization=org, is_active=True)
					if org
					else get_user_model().objects.none()
				)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser:
			obj.organization = get_user_organization(request)
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(UserProfile)
class UserProfileAdmin(AuditedAdmin):
	list_display = ("user", "organization", "department", "rut", "phone", "get_roles")
	search_fields = ("user__username", "user__first_name", "user__last_name", "rut", "phone")
	list_filter = ("organization", "department", "user__groups")
	list_select_related = ("user", "organization", "department")
	actions = [archive_selected_records]

	@admin.display(description="Roles / Grupos")
	def get_roles(self, obj):
		return ", ".join(obj.user.groups.values_list("name", flat=True)) or "Sin grupo"

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		org = get_user_organization(request)
		if not org:
			return qs.none()
		return qs.filter(organization=org, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			org = get_user_organization(request)
			if db_field.name == "organization":
				kwargs["queryset"] = Organization.objects.filter(pk=org.pk) if org else Organization.objects.none()
			elif db_field.name == "department":
				kwargs["queryset"] = (
					Department.objects.filter(organization=org, deleted_at__isnull=True)
					if org
					else Department.objects.none()
				)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser:
			obj.organization = get_user_organization(request)
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(Category)
class CategoryAdmin(AuditedAdmin):
	list_display = ("name", "is_active", "created_at")
	search_fields = ("name", "description")
	list_filter = ("is_active",)
	ordering = ("name",)
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(deleted_at__isnull=True)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(Zone)
class ZoneAdmin(AuditedAdmin):
	list_display = ("name", "organization", "limit_kwh", "is_active", "created_at")
	search_fields = ("name", "organization__legal_name")
	list_filter = ("organization", "is_active")
	ordering = ("name",)
	list_select_related = ("organization",)
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		org = get_user_organization(request)
		if not org:
			return qs.none()
		return qs.filter(organization=org, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			org = get_user_organization(request)
			if db_field.name == "organization":
				kwargs["queryset"] = Organization.objects.filter(pk=org.pk) if org else Organization.objects.none()
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser:
			obj.organization = get_user_organization(request)
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(Device)
class DeviceAdmin(AuditedAdmin):
	list_display = (
		"name",
		"serial_number",
		"organization",
		"category",
		"zone",
		"status",
		"consumption_kwh",
	)
	search_fields = ("name", "serial_number", "category__name", "zone__name")
	list_filter = ("organization", "status", "category", "zone")
	ordering = ("name",)
	list_select_related = ("organization", "category", "zone")
	actions = [archive_devices]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		organization = get_user_organization(request)
		if not organization:
			return qs.none()
		return qs.filter(organization=organization, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			organization = get_user_organization(request)
			if db_field.name == "zone":
				if organization:
					kwargs["queryset"] = Zone.objects.filter(
						organization=organization,
						deleted_at__isnull=True,
					)
				else:
					kwargs["queryset"] = Zone.objects.none()
			elif db_field.name == "organization":
				if organization:
					kwargs["queryset"] = Organization.objects.filter(pk=organization.pk)
				else:
					kwargs["queryset"] = Organization.objects.none()
			elif db_field.name == "category":
				kwargs["queryset"] = Category.objects.filter(
					is_active=True,
					deleted_at__isnull=True,
				)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser:
			obj.organization = get_user_organization(request)
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(Measurement)
class MeasurementAdmin(AuditedAdmin):
	list_display = ("device", "value_kwh", "unit", "measured_at", "source", "recorded_by")
	search_fields = ("device__name", "device__serial_number", "integration_name")
	list_filter = ("source", "device__organization")
	ordering = ("-measured_at",)
	date_hierarchy = "measured_at"
	list_select_related = ("device", "device__organization", "recorded_by")
	list_per_page = 50
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		organization = get_user_organization(request)
		if not organization:
			return qs.none()
		return qs.filter(device__organization=organization, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			organization = get_user_organization(request)
			if db_field.name == "device":
				if organization:
					kwargs["queryset"] = Device.objects.filter(
						organization=organization,
						deleted_at__isnull=True,
					)
				else:
					kwargs["queryset"] = Device.objects.none()
			elif db_field.name == "recorded_by":
				if organization:
					kwargs["queryset"] = get_user_model().objects.filter(
						profile__organization=organization,
						is_active=True,
					)
				else:
					kwargs["queryset"] = get_user_model().objects.none()
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser and not obj.recorded_by_id:
			obj.recorded_by = request.user
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(AlertRule)
class AlertRuleAdmin(AuditedAdmin):
	list_display = ("name", "category", "severity", "minimum", "maximum", "is_active")
	search_fields = ("name", "category__name")
	list_filter = ("category", "severity", "is_active")
	list_select_related = ("category",)
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == "category" and not request.user.is_superuser:
			kwargs["queryset"] = Category.objects.filter(
				is_active=True,
				deleted_at__isnull=True,
			)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(AlertEvent)
class AlertEventAdmin(AuditedAdmin):
	list_display = ("device", "rule", "status", "created_at", "resolved_by")
	search_fields = ("device__name", "rule__name", "notes")
	list_filter = ("status", "device__organization", "rule__severity")
	list_select_related = ("device", "rule", "resolved_by")
	ordering = ("-created_at",)
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		organization = get_user_organization(request)
		if not organization:
			return qs.none()
		return qs.filter(device__organization=organization, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			organization = get_user_organization(request)
			if db_field.name == "device":
				kwargs["queryset"] = (
					Device.objects.filter(organization=organization, deleted_at__isnull=True)
					if organization
					else Device.objects.none()
				)
			elif db_field.name == "measurement":
				kwargs["queryset"] = (
					Measurement.objects.filter(
						device__organization=organization, deleted_at__isnull=True
					)
					if organization
					else Measurement.objects.none()
				)
			elif db_field.name == "rule":
				kwargs["queryset"] = AlertRule.objects.filter(
					is_active=True, deleted_at__isnull=True
				)
			elif db_field.name == "resolved_by":
				kwargs["queryset"] = (
					get_user_model().objects.filter(
						profile__organization=organization, is_active=True
					)
					if organization
					else get_user_model().objects.none()
				)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser:
			if obj.status == AlertEvent.STATUS_RESOLVED and not obj.resolved_by_id:
				obj.resolved_by = request.user
				if not obj.resolved_at:
					obj.resolved_at = timezone.now()
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(AuditedAdmin):
	list_display = ("device", "organization", "request_type", "status", "priority", "assigned_to")
	search_fields = ("device__name", "device__serial_number", "reason")
	list_filter = ("organization", "request_type", "status", "priority")
	list_select_related = ("device", "organization", "assigned_to")
	actions = [archive_selected_records]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		organization = get_user_organization(request)
		if not organization:
			return qs.none()
		return qs.filter(organization=organization, deleted_at__isnull=True)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if not request.user.is_superuser:
			organization = get_user_organization(request)
			if db_field.name == "device":
				if organization:
					kwargs["queryset"] = Device.objects.filter(
						organization=organization,
						deleted_at__isnull=True,
					)
				else:
					kwargs["queryset"] = Device.objects.none()
			elif db_field.name == "organization":
				if organization:
					kwargs["queryset"] = Organization.objects.filter(pk=organization.pk)
				else:
					kwargs["queryset"] = Organization.objects.none()
			elif db_field.name == "assigned_to":
				if organization:
					kwargs["queryset"] = get_user_model().objects.filter(
						profile__organization=organization,
						is_active=True,
					)
				else:
					kwargs["queryset"] = get_user_model().objects.none()
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		if not request.user.is_superuser:
			obj.organization = get_user_organization(request)
		super().save_model(request, obj, form, change)

	def has_view_permission(self, request, obj=None):
		allowed = super().has_view_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_change_permission(self, request, obj=None):
		allowed = super().has_change_permission(request, obj)
		if not allowed:
			return False
		return check_scoped_object_permission(request.user, obj)

	def has_delete_permission(self, request, obj=None):
		return False


admin.site.site_header = "EcoEnergy Admin"
admin.site.site_title = "EcoEnergy Portal"
admin.site.index_title = "Panel de Control y Gestión Energética"
