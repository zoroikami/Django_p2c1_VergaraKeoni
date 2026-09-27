# Unidad 2 · Clase 4: Usuarios, Perfiles, Grupos y Permisos

## 🎯 Objetivo de la Clase
Implementar el modelo de autorización y roles de EcoEnergy en Django, asociando cuentas de usuario a organizaciones mediante `UserProfile` y definiendo roles con grupos y permisos según el principio de menor privilegio.

---

## 👥 Arquitectura de Identidad: User + UserProfile

1. **User (`django.contrib.auth.models.User`)**:
   - Administra credenciales (username, password, email) y estado de acceso (`is_active`, `is_staff`, `is_superuser`).
2. **UserProfile (`dispositivos.models.UserProfile`)**:
   - Modelo de dominio vinculado a `User` vía relación `OneToOneField`.
   - Conecta al usuario con su organización (`Organization`) y departamento (`Department`).
   - Auditoría histórica heredada de `BaseModel` (`created_at`, `updated_at`, `deleted_at`).
   - Validación en `clean()`: garantiza que el departamento asignado pertenezca a la misma organización que el usuario.

---

## 🛡️ Matriz de Roles y Permisos (EcoEnergy)

| Rol | Responsabilidad | Modelos Afectados | Permisos Asignados |
| :--- | :--- | :--- | :--- |
| **Administrador Organizacional** | Configuración operativa completa de su organización | Categorías, Zonas, Dispositivos, Departamentos, Mediciones, Reglas de Alerta, Eventos, Mantenimiento, Perfiles | `add_*`, `change_*`, `view_*` en entidades operativas. **Sin permisos de borrado físico.** |
| **Operador** | Registro de consumos, seguimiento de dispositivos y atención de alertas | Dispositivos, Zonas, Categorías, Mediciones, Eventos de Alerta, Solicitudes de Mantenimiento | `view_device`, `view_zone`, `view_category`, `add_measurement`, `view_measurement`, `change_alertevent`, `view_alertevent`, `add_maintenancerequest`, `change_maintenancerequest`, `view_maintenancerequest`. **Sin permisos de modificación ni eliminación de dispositivos ni mediciones.** |
| **Consulta** | Supervisión y auditoría en modo sólo lectura | Dispositivos, Mediciones, Eventos, Reglas, Zonas, Categorías, Organización, Departamentos | Exclusivamente permisos `view_*` en todos los modelos consultables. |

---

## 🚀 Comando de Configuración
Para aprovisionar los grupos, permisos y usuarios de prueba con acceso al Django Admin (`is_staff=True`):

```bash
python manage.py setup_roles
```

### Usuarios de Prueba Creados:
- `admin_demo` (Contraseña: `Password123!`) → Rol: **Administrador Organizacional**
- `operador_demo` (Contraseña: `Password123!`) → Rol: **Operador**
- `consulta_demo` (Contraseña: `Password123!`) → Rol: **Consulta**

---

## 🎫 Ticket de Salida (Clase 4)
**¿Cómo explicarías la diferencia entre User, UserProfile, Group y Permission usando uno de tus usuarios de prueba?**

- **User**: Representa la cuenta técnica y de autenticación (`operador_demo`), maneja su clave y permite iniciar sesión.
- **UserProfile**: Extiende la identidad en el dominio EcoEnergy, asignando a `operador_demo` a la empresa *EcoEnergy Demo SpA* y departamento *Operaciones*.
- **Group**: Es la agrupación de rol `Operador`, permitiendo reutilizar un conjunto coherente de facultades para múltiples operarios.
- **Permission**: Es la autorización granular otorgada al grupo (por ejemplo, `add_measurement` para registrar consumos, y la ausencia deliberada de `delete_measurement` para proteger la trazabilidad).
