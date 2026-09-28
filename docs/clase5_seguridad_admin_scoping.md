# Unidad 2 · Clase 5: Seguridad en Django Admin y Scoping de Datos

## 🎯 Objetivo de la Clase
Implementar seguridad contextual y aislamiento multi-tenant en Django Admin mediante QuerySets acotados por organización, relaciones (ForeignKeys) filtradas en formularios, asignación automática del ámbito en `save_model`, permisos a nivel de objeto, acciones de borrado lógico y componentes Inline.

---

## 🛡️ Arquitectura de Seguridad en Múltiples Capas

```text
[ 1. PERMISOS (Group / Permission) ]  --> ¿Puede el usuario ejecutar la operación (view/add/change)?
                 ↓
[ 2. QUERYSET (get_queryset) ]         --> ¿Qué registros de su organización están autorizados y no archivados?
                 ↓
[ 3. FORMULARIO (formfield_for_fk) ]   --> ¿Qué opciones relacionadas puede elegir en los selectores?
                 ↓
[ 4. GUARDADO (save_model) ]           --> Asignación forzada de la organización desde el perfil del usuario.
                 ↓
[ 5. OBJETO (has_change_permission) ]  --> Comprobación de propiedad para prevenir accesos forzados por URL directas.
                 ↓
[ 6. POLÍTICA DE BORRADO ]             --> has_delete_permission=False + Acción personalizada de archivado lógico.
```

---

## 🧩 Implementaciones Clave

### 1. Función Auxiliar `get_user_organization(request)`
Ubicada en `core/admin_utils.py` y `dispositivos/admin_utils.py`:
- **Superusuario:** retorna `None` (mantiene visibilidad global de todas las empresas para auditoría técnica).
- **Usuario Operativo con Perfil:** retorna la instancia de `Organization` asignada.
- **Usuario sin Perfil:** retorna `None` de forma segura (impide fugas de información devolviendo consultas vacías `qs.none()`).

### 2. Acotamiento de QuerySets (`get_queryset`)
- Filtra por `organization=organization` (o `device__organization=organization`).
- Excluye registros marcados como eliminados: `deleted_at__isnull=True`.

### 3. Filtro en Claves Foráneas (`formfield_for_foreignkey`)
- En `MeasurementAdmin`, el selector del campo `device` únicamente despliega dispositivos activos pertenecientes a la organización del usuario autenticado.
- En `DeviceAdmin` y `UserProfileAdmin`, los selectores de `zone`, `department` y `organization` se restringen al ámbito correspondiente.

### 4. Asignación Automática del Ámbito (`save_model`)
- El valor de la organización no proviene del navegador ni de campos editables por el operador; se asigna forzosamente desde `get_user_organization(request)`.
- En mediciones manuales, el campo `recorded_by` se vincula automáticamente a `request.user`.

### 5. Control de Permisos por Objeto (`has_change_permission`)
- Valida en primera instancia el permiso general (`change_device`, etc.).
- Valida en segunda instancia que el registro consultado pertenezca a la organización del usuario (`obj.organization_id == organization.id`), bloqueando intentos de acceso por ID directo en la URL.

### 6. Política de Borrado Lógico
- `has_delete_permission(request, obj=None)` retorna `False` para bloquear la eliminación física de registros.
- Se implementan acciones `@admin.action(permissions=["change"])`:
  - `archive_devices`: archiva dispositivos estableciendo `deleted_at = timezone.now()`.
  - `archive_selected_records`: acción genérica para entidades con `BaseModel`.

### 7. Inline Administrativo (`DepartmentInline`)
- `DepartmentInline(admin.TabularInline)` registrado dentro de `OrganizationAdmin`, facilitando la gestión padre-hijo de departamentos directamente desde la organización.

---

## 🧪 Demostración y Pruebas Multi-Organización

Se dispone del comando para cargar el escenario completo con dos organizaciones independientes (*Norte* y *Sur*):

```bash
python manage.py seed_data
```

### Matriz de Usuarios para Pruebas:
| Usuario | Rol | Ámbito | Comportamiento en Admin |
| :--- | :--- | :--- | :--- |
| `admin` | Superusuario | Global | Visualiza y administra todas las organizaciones, zonas, dispositivos y mediciones (incluso archivados). |
| `admin_norte` | Admin Org | EcoEnergy Norte | Gestiona configuración, dispositivos y departamentos exclusivamente de *EcoEnergy Norte*. |
| `operador_norte` | Operador | EcoEnergy Norte | Consulta dispositivos Norte, registra mediciones para equipos Norte. No ve ni puede acceder a equipos Sur. |
| `consulta_norte` | Consulta | EcoEnergy Norte | Modo sólo lectura de registros Norte. No puede agregar ni modificar datos. |
| `operador_sur` | Operador | EcoEnergy Sur | Consulta y registra mediciones exclusivamente para *EcoEnergy Sur*. |
| `staff_sin_perfil` | Staff sin perfil | N/A | Caso de prueba negativa: no recibe ningún registro (`queryset.none()`), denegación segura. |

*(Contraseña general de prueba: `Password123!`; superusuario: `Admin123!`)*

---

## 🎫 Ticket de Salida (Clase 5)
**¿Cuál es la prueba negativa más importante implementada y qué riesgo previene?**

- **Prueba Negativa:** Intentar acceder mediante URL directa o modificar un objeto perteneciente a otra organización (por ejemplo, `operador_norte` intentando consultar o alterar `dev_sur_1`).
- **Comprobación:** `has_change_permission` rechaza la solicitud al evaluar que `obj.organization_id != user.profile.organization_id`, y el formulario de mediciones excluye en `formfield_for_foreignkey` cualquier equipo foráneo.
- **Riesgo Prevenido:** Fuga de datos (*data leakage*) e interferencia operativa entre clientes distintos en una plataforma compartida (aislamiento multi-tenant).
