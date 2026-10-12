import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import (
    DeviceForm,
    PasswordResetRequestForm,
    PasswordResetVerifyForm,
    PasswordResetConfirmForm,
)
from .models import Device, PasswordResetCode
from .services import listar_zonas_con_resumen, obtener_zona_detalle


def _get_user_organization(user):
    """Obtiene la organización asociada al perfil del usuario autenticado."""
    if user.is_authenticated and hasattr(user, "profile") and user.profile:
        return user.profile.organization
    return None


def custom_403(request, exception=None):
    """Manejador global de respuesta HTTP 403 Forbidden (Clase 7)."""
    return render(request, "403.html", status=403)


def custom_404(request, exception=None):
    """Manejador global de respuesta HTTP 404 Not Found."""
    return render(request, "404.html", status=404)


# ==============================================================================
# Vistas de Inicio y Exploración (Clase 6 - Sesiones y Navegación)
# ==============================================================================

def inicio(request):
    """
    Página de inicio con registro de visitas temporales en la sesión (Clase 6).
    """
    visits = request.session.get("inicio_visits", 0) + 1
    request.session["inicio_visits"] = visits

    contexto = {
        "sistema": "EcoEnergy",
        "mensaje": "Monitoreo energético responsable",
        "asignatura": "Programación Back End",
        "visits": visits,
    }
    return render(request, "dispositivos/inicio.html", contexto)


def zonas(request):
    org = _get_user_organization(request.user)
    org_id = org.pk if org else None
    zonas_list = listar_zonas_con_resumen(org_id)
    return render(request, "dispositivos/zonas.html", {"zonas": zonas_list})


def zona_detalle(request, zona_id):
    org = _get_user_organization(request.user)
    org_id = org.pk if org else None
    detalle = obtener_zona_detalle(zona_id, org_id)
    if detalle is None:
        raise Http404("Zona no encontrada")

    return render(request, "dispositivos/zona_detalle.html", detalle)


def resumen_zonas(request, zona_id=None):
    org = _get_user_organization(request.user)
    org_id = org.pk if org else None
    if zona_id is not None:
        detalle = obtener_zona_detalle(zona_id, org_id)
        if detalle is None:
            raise Http404("Zona no encontrada")
        return render(request, "dispositivos/resumen_zonas.html", detalle)

    zonas_list = listar_zonas_con_resumen(org_id)
    return render(request, "dispositivos/resumen_zonas.html", {"zonas": zonas_list})


# ==============================================================================
# Desafío: Recuperación de Contraseña con Código Temporal (Clase 6)
# ==============================================================================

def password_reset_request(request):
    """
    Paso 1: Solicitar recuperación ingresando correo.
    Genera un código no predecible de 6 dígitos, lo almacena hasheado con TTL de 120s
    y responde de forma genérica para evitar enumeración de usuarios.
    """
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            User = get_user_model()
            users = User.objects.filter(email__iexact=email, is_active=True)

            if users.exists():
                user = users.first()
                # Invalidar códigos previos activos del usuario
                PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

                # Generar código numérico de 6 dígitos con secrets
                code = f"{secrets.randbelow(1000000):06d}"
                ttl = getattr(settings, "PASSWORD_RESET_CODE_TTL_SECONDS", 120)
                expires_at = timezone.now() + timedelta(seconds=ttl)

                reset_obj = PasswordResetCode.objects.create(
                    user=user,
                    code_hash=make_password(code),
                    expires_at=expires_at,
                )

                # Envío de correo mediante el backend configurado
                subject = "Código de Recuperación de Acceso - EcoEnergy"
                body = (
                    f"Hola {user.get_full_name() or user.username},\n\n"
                    f"Has solicitado restablecer tu contraseña. Tu código de verificación es:\n\n"
                    f"    {code}\n\n"
                    f"Este código es de un solo uso y expirará en {ttl} segundos.\n"
                    f"Si tú no realizaste esta solicitud, por favor desestima este correo.\n\n"
                    f"Equipo de Seguridad EcoEnergy"
                )
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ecoenergy.local"),
                    recipient_list=[email],
                    fail_silently=False,
                )

                request.session["reset_email"] = email
                request.session["reset_code_id"] = reset_obj.pk
            else:
                # Mantener la respuesta genérica incluso si el correo no existe
                request.session["reset_email"] = email

            messages.info(
                request,
                "Si la dirección de correo coincide con una cuenta activa, recibirás un código de 6 dígitos.",
            )
            return redirect("dispositivos:password_reset_verify")
    else:
        form = PasswordResetRequestForm()

    return render(request, "dispositivos/password_reset_request.html", {"form": form})


def password_reset_verify(request):
    """
    Paso 2: Validar el código de 6 dígitos dentro de su ventana de vigencia (120 s).
    Controla código inválido, expirado, ya utilizado y límite de intentos fallidos.
    """
    email = request.session.get("reset_email")
    if not email:
        messages.warning(request, "Debes solicitar un código de recuperación primero.")
        return redirect("dispositivos:password_reset_request")

    if request.method == "POST":
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            max_attempts = getattr(settings, "PASSWORD_RESET_MAX_ATTEMPTS", 5)

            # Buscar la solicitud activa más reciente asociada a este correo
            reset_entry = (
                PasswordResetCode.objects.filter(
                    user__email__iexact=email,
                    is_used=False,
                )
                .order_by("-created_at")
                .first()
            )

            if not reset_entry:
                form.add_error("code", "No existe una solicitud de recuperación vigente para este correo.")
            elif reset_entry.is_blocked(max_attempts):
                form.add_error("code", "Has superado el máximo de intentos permitidos. Solicita un nuevo código.")
            elif reset_entry.is_expired():
                form.add_error("code", "El código ha expirado. Por favor, solicita uno nuevo.")
            elif not reset_entry.check_code(code):
                reset_entry.failed_attempts += 1
                reset_entry.save(update_fields=["failed_attempts"])
                remaining = max_attempts - reset_entry.failed_attempts
                if remaining > 0:
                    form.add_error("code", f"Código incorrecto. Intentos restantes: {remaining}.")
                else:
                    form.add_error("code", "Has superado el límite de intentos. El código ha sido bloqueado.")
            else:
                # Código válido y vigente: autorizar paso de cambio de contraseña
                request.session["reset_verified_code_id"] = reset_entry.pk
                messages.success(request, "Código validado exitosamente. Ingresa tu nueva contraseña.")
                return redirect("dispositivos:password_reset_confirm")
    else:
        form = PasswordResetVerifyForm()

    ttl = getattr(settings, "PASSWORD_RESET_CODE_TTL_SECONDS", 120)
    return render(
        request,
        "dispositivos/password_reset_verify.html",
        {"form": form, "email": email, "ttl_seconds": ttl},
    )


def password_reset_confirm(request):
    """
    Paso 3: Definir nueva contraseña con validaciones de Django e invalidar código.
    """
    code_id = request.session.get("reset_verified_code_id")
    if not code_id:
        messages.error(request, "Sesión de verificación no válida o expirada.")
        return redirect("dispositivos:password_reset_request")

    reset_entry = get_object_or_404(PasswordResetCode, pk=code_id, is_used=False)

    if request.method == "POST":
        form = PasswordResetConfirmForm(reset_entry.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            user = reset_entry.user

            # Guardar contraseña de forma segura
            user.set_password(new_password)
            user.save()

            # Consumir el código temporal inmediatamente (un solo uso)
            reset_entry.is_used = True
            reset_entry.used_at = timezone.now()
            reset_entry.save(update_fields=["is_used", "used_at"])

            # Limpiar variables temporales de la sesión
            request.session.pop("reset_email", None)
            request.session.pop("reset_code_id", None)
            request.session.pop("reset_verified_code_id", None)

            messages.success(
                request,
                "Tu contraseña ha sido restablecida con éxito. Inicia sesión con tus nuevas credenciales.",
            )
            return redirect("login")
    else:
        form = PasswordResetConfirmForm(reset_entry.user)

    return render(request, "dispositivos/password_reset_confirm.html", {"form": form})


# ==============================================================================
# CRUD Completo Protegido con ModelForm, Modal Bootstrap y SweetAlert2 (Clases 7 y 8)
# ==============================================================================

class ScopedPermissionMixin:
    """
    Mixin que asegura que usuarios anónimos sean redirigidos a LOGIN_URL (302)
    y los usuarios autenticados sin permiso reciban HTTP 403 Forbidden (Clases 6 y 7).
    """
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        raise PermissionDenied(self.get_permission_denied_message())


class DeviceListView(ScopedPermissionMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Listado protegido con scoping multi-tenant y exclusión de borrado lógico (Clases 7 y 8).
    """
    model = Device
    template_name = "dispositivos/catalogo.html"
    context_object_name = "dispositivos"
    permission_required = "dispositivos.view_device"
    raise_exception = True

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = Device.objects.filter(deleted_at__isnull=True)
        else:
            org = _get_user_organization(user)
            if not org:
                return Device.objects.none()
            qs = Device.objects.filter(organization=org, deleted_at__isnull=True)

        return qs.select_related("organization", "zone", "category").order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dispositivos = list(context["dispositivos"])
        activos = sum(1 for d in dispositivos if d.status == Device.STATUS_ACTIVE)
        context["total"] = len(dispositivos)
        context["total_activos"] = activos

        # Contador de visitas de sesión a la vista de dispositivos (Clase 6)
        visits = self.request.session.get("catalog_visits", 0) + 1
        self.request.session["catalog_visits"] = visits
        context["catalog_visits"] = visits

        # Instanciar formulario vacío para el modal de creación si tiene permiso
        if "form" not in context and self.request.user.has_perm("dispositivos.add_device"):
            context["form"] = DeviceForm(user=self.request.user)

        return context


class DeviceCreateView(ScopedPermissionMixin, LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Creación protegida de dispositivos utilizando ModelForm en Modal Bootstrap (Clase 8).
    """
    model = Device
    form_class = DeviceForm
    template_name = "dispositivos/catalogo.html"
    success_url = reverse_lazy("dispositivos:catalogo")
    success_message = "Dispositivo '%(name)s' registrado exitosamente."
    permission_required = "dispositivos.add_device"
    raise_exception = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        org = _get_user_organization(user)
        if org and not user.is_superuser:
            form.instance.organization = org
        return super().form_valid(form)

    def form_invalid(self, form):
        """En caso de error de validación, re-renderiza el catálogo con el modal abierto y los errores."""
        list_view = DeviceListView()
        list_view.request = self.request
        context = list_view.get_context_data(object_list=list_view.get_queryset())
        context["form"] = form
        context["open_modal"] = True
        return render(self.request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Si se accede vía GET /dispositivos/new/, renderiza el catálogo con el modal abierto."""
        list_view = DeviceListView()
        list_view.request = self.request
        context = list_view.get_context_data(object_list=list_view.get_queryset())
        context["form"] = self.get_form()
        context["open_modal"] = True
        return context


class DeviceUpdateView(ScopedPermissionMixin, LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Edición protegida de dispositivos reutilizando el ModelForm y Modal Bootstrap (Clase 8).
    """
    model = Device
    form_class = DeviceForm
    template_name = "dispositivos/catalogo.html"
    success_url = reverse_lazy("dispositivos:catalogo")
    success_message = "Dispositivo '%(name)s' actualizado exitosamente."
    permission_required = "dispositivos.change_device"
    raise_exception = True

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Device.objects.filter(deleted_at__isnull=True)
        org = _get_user_organization(user)
        if not org:
            return Device.objects.none()
        return Device.objects.filter(organization=org, deleted_at__isnull=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        """En caso de error de validación, re-renderiza el catálogo con el modal de edición abierto."""
        list_view = DeviceListView()
        list_view.request = self.request
        context = list_view.get_context_data(object_list=list_view.get_queryset())
        context["form"] = form
        context["object"] = self.get_object()
        context["open_modal"] = True
        return render(self.request, self.template_name, context)

    def get_context_data(self, **kwargs):
        list_view = DeviceListView()
        list_view.request = self.request
        context = list_view.get_context_data(object_list=list_view.get_queryset())
        context["form"] = self.get_form()
        context["object"] = self.get_object()
        context["open_modal"] = True
        return context


class DeviceDeleteView(ScopedPermissionMixin, LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Eliminación protegida con confirmación vía SweetAlert2 y borrado lógico (Clase 8).
    """
    model = Device
    success_url = reverse_lazy("dispositivos:catalogo")
    success_message = "Dispositivo eliminado correctamente."
    permission_required = "dispositivos.delete_device"
    raise_exception = True

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Device.objects.filter(deleted_at__isnull=True)
        org = _get_user_organization(user)
        if not org:
            return Device.objects.none()
        return Device.objects.filter(organization=org, deleted_at__isnull=True)

    def form_valid(self, form):
        """Aplica borrado lógico marcando deleted_at en lugar de eliminación física."""
        self.object = self.get_object()
        self.object.deleted_at = timezone.now()
        self.object.save(update_fields=["deleted_at"])
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())

    def delete(self, request, *args, **kwargs):
        return self.form_valid(None)
