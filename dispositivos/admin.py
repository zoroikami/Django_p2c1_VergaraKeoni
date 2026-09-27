from django.contrib import admin

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


class AuditedAdmin(admin.ModelAdmin):
	readonly_fields = ("created_at", "updated_at", "deleted_at")


@admin.register(Organization)
class OrganizationAdmin(AuditedAdmin):
	list_display = ("legal_name", "tax_id", "trade_name", "is_active")
	search_fields = ("legal_name", "tax_id", "trade_name")
	list_filter = ("is_active",)
	ordering = ("legal_name",)


@admin.register(Department)
class DepartmentAdmin(AuditedAdmin):
	list_display = ("name", "organization", "manager", "is_active")
	search_fields = ("name", "organization__legal_name", "manager__username")
	list_filter = ("organization", "is_active")
	list_select_related = ("organization", "manager")


@admin.register(UserProfile)
class UserProfileAdmin(AuditedAdmin):
	list_display = ("user", "organization", "department", "rut", "phone", "get_roles")
	search_fields = ("user__username", "user__first_name", "user__last_name", "rut", "phone")
	list_filter = ("organization", "department", "user__groups")
	list_select_related = ("user", "organization", "department")

	@admin.display(description="Roles / Grupos")
	def get_roles(self, obj):
		return ", ".join(obj.user.groups.values_list("name", flat=True)) or "Sin grupo"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "is_active", "created_at")
	search_fields = ("name", "description")
	list_filter = ("is_active",)
	ordering = ("name",)
	readonly_fields = ("created_at", "updated_at")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
	list_display = ("name", "organization", "limit_kwh", "is_active", "created_at")
	search_fields = ("name", "organization__legal_name")
	list_filter = ("organization", "is_active")
	ordering = ("name",)
	list_select_related = ("organization",)
	readonly_fields = ("created_at", "updated_at")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
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
	readonly_fields = ("created_at", "updated_at")


@admin.register(Measurement)
class MeasurementAdmin(AuditedAdmin):
	list_display = ("device", "value_kwh", "unit", "measured_at", "source", "recorded_by")
	search_fields = ("device__name", "device__serial_number", "integration_name")
	list_filter = ("source", "device__organization")
	ordering = ("-measured_at",)
	date_hierarchy = "measured_at"
	list_select_related = ("device", "device__organization", "recorded_by")
	list_per_page = 50


@admin.register(AlertRule)
class AlertRuleAdmin(AuditedAdmin):
	list_display = ("name", "category", "severity", "minimum", "maximum", "is_active")
	search_fields = ("name", "category__name")
	list_filter = ("category", "severity", "is_active")
	list_select_related = ("category",)


@admin.register(AlertEvent)
class AlertEventAdmin(AuditedAdmin):
	list_display = ("device", "rule", "status", "created_at", "resolved_by")
	search_fields = ("device__name", "rule__name", "notes")
	list_filter = ("status", "device__organization", "rule__severity")
	list_select_related = ("device", "rule", "resolved_by")
	ordering = ("-created_at",)


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(AuditedAdmin):
	list_display = ("device", "organization", "request_type", "status", "priority", "assigned_to")
	search_fields = ("device__name", "device__serial_number", "reason")
	list_filter = ("organization", "request_type", "status", "priority")
	list_select_related = ("device", "organization", "assigned_to")
