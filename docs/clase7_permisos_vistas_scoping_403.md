# Unidad 2 · Clase 7: Autorización en Vistas, Grupos, Scoping y Manejo de Error 403

## 🎯 Objetivo de Aprendizaje
Proteger las vistas y operaciones de usuario final en Django utilizando autenticación obligatoria, verificación de capacidades granulares mediante permisos/grupos, acotamiento estricto de datos (scoping multi-tenant) y respuestas HTTP 403/404 coherentes.

---

## 🛡️ 1. Las Tres Capas de Seguridad en una Vista

1. **¿Quién eres? (Autenticación):**
   * Verificado mediante `LoginRequiredMixin` y decorador `@login_required`.
   * Si el visitante es anónimo, se le redirige a `LOGIN_URL` con el parámetro `next`.
2. **¿Qué puedes hacer? (Autorización):**
   * Verificado mediante `PermissionRequiredMixin` y permisos concretos (`dispositivos.view_device`, `add_device`, `change_device`, `delete_device`).
   * **Uso de `raise_exception=True` / `ScopedPermissionMixin`:** Si un usuario autenticado carece del permiso requerido, Django no lo confunde redirigiéndolo al login; responde inmediatamente con **HTTP 403 Forbidden**.
3. **¿Sobre qué datos? (Scoping Multi-Tenant):**
   * Los permisos indican capacidades, no objetos. El QuerySet en `get_queryset()` se filtra obligatoriamente por la organización del usuario (`organization=request.user.profile.organization`) y por `deleted_at__isnull=True`.
   * En operaciones individuales por clave primaria (`<int:pk>`), los objetos fuera del ámbito organizacional del usuario devuelven **HTTP 404 Not Found**, impidiendo a terceros descubrir registros pertenecientes a otras empresas.

---

## 🚫 2. Manejador de Error 403 Personalizado

* **Configuración global:** `handler403 = 'dispositivos.views.custom_403'` en `config/urls.py`.
* **Vista:** `custom_403(request, exception=None)` renderiza la plantilla `templates/403.html` con status HTTP 403.
* **Experiencia de Usuario:** La página explica de manera comprensible que la cuenta carece de privilegios o que el recurso no pertenece a su organización, sin revelar trazas internas ni información confidencial del sistema.

---

## 🎨 3. Adaptación de Interfaz con `perms`

En las plantillas (`templates/dispositivos/catalogo.html`), los botones de acción se condicionan mediante el contexto de permisos de Django:
* **Botón "Nuevo Dispositivo":** Visible únicamente con `{% if perms.dispositivos.add_device %}`.
* **Botón "Editar":** Visible únicamente con `{% if perms.dispositivos.change_device %}`.
* **Botón "Eliminar":** Visible únicamente con `{% if perms.dispositivos.delete_device %}`.

> **Principio Clave:** Ocultar un botón en el template mejora la experiencia de usuario (UX), pero la View en el servidor es la barrera definitiva que valida la autorización ante cualquier petición directa.

---

## 👥 4. Matriz de Roles y Comportamiento Demostrado

| Rol de Usuario | Usuario Demo | `view_device` | `add_device` | `change_device` | `delete_device` | Resultado al Intentar Borrar |
| :--- | :--- | :-: | :-: | :-: | :-: | :--- |
| **Superusuario Global** | `admin` | Sí | Sí | Sí | Sí | Permitido (Borrado lógico) |
| **Administrador Org.** | `admin_norte` | Sí | Sí | Sí | No | **HTTP 403 Forbidden** |
| **Operador** | `operador_norte` | Sí | No | No | No | **HTTP 403 Forbidden** |
| **Consulta (Solo Lectura)** | `consulta_norte` | Sí | No | No | No | **HTTP 403 Forbidden** en Crear/Editar/Borrar |
| **Anónimo** | Sin sesión | No | No | No | No | **HTTP 302 Redirect** a Login |
