# Unidad 2 · Clase 8: CRUD Completo Protegido + ModelForm + Modal Bootstrap + SweetAlert2

## 🎯 Objetivo de Aprendizaje
Construir las operaciones CRUD completas (Crear, Listar, Editar, Eliminar) para la entidad central `Device` fuera del Django Admin, integrando validaciones robustas de ModelForm, una interfaz interactiva con modal Bootstrap reutilizable y confirmaciones profesionales mediante SweetAlert2.

---

## 🏗️ 1. Arquitectura de Vistas Basadas en Clases (CBV)

Se implementaron Vistas Basadas en Clases (CBV) con composición de mixins de seguridad:

1. **`DeviceListView` (`ListView`):**
   * Mixins: `ScopedPermissionMixin`, `LoginRequiredMixin`, `PermissionRequiredMixin`.
   * Permiso: `dispositivos.view_device`.
   * Scoping: Filtra el QuerySet por la organización del usuario (`organization=user.profile.organization`) y excluye registros archivados (`deleted_at__isnull=True`).
   * Optimización: `select_related('organization', 'zone', 'category')`.
2. **`DeviceCreateView` (`CreateView`):**
   * Mixins: `ScopedPermissionMixin`, `LoginRequiredMixin`, `PermissionRequiredMixin`, `SuccessMessageMixin`.
   * Permiso: `dispositivos.add_device`.
   * Asignación automática: En `form_valid()`, asigna la organización del usuario automáticamente antes de guardar.
   * Manejo de modal: Si el formulario es inválido (`form_invalid`), re-renderiza el catálogo pasando `open_modal=True` para conservar los errores visibles dentro del modal sin recargar la página.
3. **`DeviceUpdateView` (`UpdateView`):**
   * Mixins: `ScopedPermissionMixin`, `LoginRequiredMixin`, `PermissionRequiredMixin`, `SuccessMessageMixin`.
   * Permiso: `dispositivos.change_device`.
   * Scoping: `get_queryset()` restringido estrictamente a la organización del usuario. Si un usuario intenta editar un ID de otra empresa, recibe HTTP 404.
   * Reutilización: Utiliza el mismo `DeviceForm` y el mismo partial de modal.
4. **`DeviceDeleteView` (`DeleteView`):**
   * Mixins: `ScopedPermissionMixin`, `LoginRequiredMixin`, `PermissionRequiredMixin`, `SuccessMessageMixin`.
   * Permiso: `dispositivos.delete_device`.
   * Scoping: Acotado a la organización del usuario.
   * **Borrado Lógico:** Sobrescribe `form_valid()` marcando `deleted_at = timezone.now()` en el objeto `BaseModel`. El registro no se borra físicamente, manteniendo trazabilidad e integridad referencial.

---

## 📝 2. Validaciones en `DeviceForm` (`forms.ModelForm`)

* **Etiquetas y Widgets:** Campos formateados con clases de Bootstrap 5 (`form-control`, `form-select`).
* **Scoping en Selectores:** En `__init__`, los QuerySets de `zone` y `category` se filtran para mostrar únicamente las zonas pertenecientes a la organización del usuario y categorías activas.
* **`clean_name()`:**
  * Validación de longitud mínima ($\ge 3$ caracteres).
  * Unicidad case-insensitive por organización (`name__iexact=name`), excluyendo la propia instancia en modo edición (`exclude(pk=self.instance.pk)`).
* **`clean_serial_number()`:**
  * Unicidad de número de serie activo en el sistema.
* **`clean()`:**
  * Valida coherencia organizacional entre dispositivo y zona seleccionada.
  * Valida que el consumo energético no sea negativo.

---

## 🪟 3. Modal Bootstrap Reutilizable (`_device_form_modal.html`)

* **Reutilización:** Se utiliza un único partial template para creación y edición.
  * Si existe `object`, el título es *"Editar Dispositivo"*; si no, *"Nuevo Dispositivo"*.
* **Persistencia de Errores:**
  * Los errores generales se muestran en `{{ form.non_field_errors }}`.
  * Cada campo renderiza sus errores correspondientes con `{{ error }}` en color rojo.
* **Apertura Automática:** Si la vista envía `open_modal=True` (en GET de edición o tras fallar la validación en POST), un script de JavaScript ejecuta `new bootstrap.Modal(...).show()`.

---

## ⚡ 4. Confirmación de Eliminación con SweetAlert2

* **Flujo Seguro:**
  1. El usuario presiona el botón "Eliminar".
  2. La función JavaScript `confirmDelete(id, name)` invoca `Swal.fire({ title: '¿Eliminar dispositivo?', ... })`.
  3. Si el usuario confirma, JavaScript hace el `.submit()` de un formulario POST oculto con token CSRF hacia `{% url 'dispositivos:device_delete' d.pk %}`.
  4. El servidor valida la identidad, el permiso `delete_device` y el ámbito organizacional antes de ejecutar el borrado lógico.
  5. El usuario es redirigido con un mensaje de confirmación de éxito.
