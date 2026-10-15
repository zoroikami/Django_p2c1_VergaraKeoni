# EcoEnergy - Sistema de Monitoreo Energético Responsable

Proyecto Back End desarrollado con **Python** y **Django** para la asignatura **Programación Back End**.

---

## 🎯 Descripción y Objetivo

**EcoEnergy** administra organizaciones, departamentos, zonas, dispositivos y mediciones de consumo. Incluye un Django Admin con permisos por organización, validaciones de negocio y archivado lógico.

---

## 📋 Requisitos Previos

- **Python 3.12** o superior instalado en el sistema.
- **Git** instalado.

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonación del Repositorio

```bash
git clone https://github.com/zoroikami/Django_p2c1_VergaraKeoni.git
cd Django_p2c1_VergaraKeoni
```

### 2. Creación y Activación del Entorno Virtual (`.venv`)

- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

- **Windows (CMD):**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate.bat
  ```

- **Linux / macOS / Git Bash:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalación de dependencias y datos de demostración

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Copiar `.env.example` a `.env` (PowerShell: `Copy-Item .env.example .env`; macOS/Linux: `cp .env.example .env`). La configuración de ejemplo usa SQLite. Después ejecutar:

```bash
python manage.py check
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

En desarrollo, `runserver` activa `DEBUG` por defecto si `DJANGO_DEBUG` no está definido, para que
los estilos y scripts del panel de administración se sirvan correctamente.
`DJANGO_DEBUG=false` lo desactiva de forma explícita; fuera de `runserver`, el
valor predeterminado sigue siendo `false`.

`seed_data` puede ejecutarse varias veces: actualiza los datos de demostración sin duplicar las ocho mediciones y vuelve a dejar activos los ocho dispositivos de la demo. Agrega **EcoEnergy Norte** y **EcoEnergy Sur**, cuatro zonas, tres categorías, un dispositivo archivado (`SN-NTE-ARCH-001`), departamentos y las cuentas indicadas abajo. Una migración histórica también puede conservar la organización técnica `Legacy EcoEnergy Organization`; no forma parte de la demo. La base SQLite se genera localmente y no se versiona.

---

## 🔍 Comandos de Verificación

1. **Comprobar la configuración del proyecto:**
   ```bash
   python manage.py check
   ```

2. **Iniciar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

3. **Verificar las rutas en el navegador:**
   - **Inicio:** `http://127.0.0.1:8000/` (muestra datos del sistema mediante contexto).
   - **Catálogo de Dispositivos:** `http://127.0.0.1:8000/dispositivos/` (muestra la lista de dispositivos registrados).

---

## 📁 Estructura del Proyecto

```text
Django_p2c1_VergaraKeoni/
├── config/
│   ├── settings.py       # Configuración global y registro de templates
│   ├── urls.py           # Enrutador principal
│   ├── wsgi.py
│   └── asgi.py
├── core/admin_utils.py  # Organización del usuario actual
├── dispositivos/
│   ├── models.py         # Entidades, auditoría y validaciones clean()
│   ├── admin.py          # Admin, Inline, acciones y scoping
│   ├── roles.py          # Grupos y permisos
│   ├── management/commands/seed_data.py
│   ├── migrations/       # Esquema versionado
│   ├── tests.py
│   ├── views.py
│   └── urls.py
├── templates/
│   ├── base.html
│   └── dispositivos/
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

---

## 📌 Estado Actual del Proyecto (Unidad 2 Completa - Clases 1 a 10)

El proyecto cuenta con la implementación completa de las **10 clases de la Unidad 2**:
- **Clase 1 (Modelo de Datos y Arquitectura):** Modelos de negocio con `BaseModel` abstracto (`created_at`, `updated_at`, `deleted_at`) y diseño modular.
- **Clase 2 (Modelos y Migraciones):** Soporte multi-motor (SQLite/MySQL) vía `.env`, constraints de unicidad, índices y migraciones aplicadas.
- **Clase 3 (Django Admin Básico):** Administración con `list_display`, `search_fields` cruzando relaciones, `list_filter`, `list_select_related`, `date_hierarchy` y representaciones `__str__` legibles.
- **Clase 4 (Usuarios, Perfiles y Roles):** Integración `User + UserProfile` con validación organizacional en `clean()`, y roles con grupos (`Administrador Organizacional`, `Operador`, `Consulta`) bajo el principio de menor privilegio.
- **Clase 5 (Seguridad en Admin y Scoping):** Aislamiento multi-tenant con `get_queryset` acotado por organización, exclusión de borrado lógico, `formfield_for_foreignkey` restrictivo, auto-asignación en `save_model`, permisos por objeto (`has_change_permission`), acción de archivado y `DepartmentInline`.
- **Clase 6 (Autenticación, Sesiones y Recuperación):**
  - Autenticación de usuario final con `LoginView`, logout seguro vía POST con CSRF y navegación condicional en `base.html`.
  - Integración del framework de mensajes adaptado a Bootstrap 5 (`alert-{{ message.tags }}`).
  - Manejo de estado temporal en `request.session` (conteo de visitas en sesión).
  - **Desafío de Recuperación de Contraseña:** Generación segura con `secrets` de códigos de 6 dígitos numéricos, almacenamiento hasheado (`make_password`), vigencia de 120 segundos, control de un solo uso, límite de 5 intentos fallidos y entrega por correo (Consola / Mailtrap).
- **Clase 7 (Autorización en Vistas, Grupos y 403):**
  - Protección granular en vistas mediante `LoginRequiredMixin` y `PermissionRequiredMixin`.
  - Redirección de visitantes anónimos al login (HTTP 302) y denegación con **HTTP 403 Forbidden** a usuarios autenticados sin permiso.
  - Manejador global `handler403` y plantilla personalizada `templates/403.html`.
  - Scoping de QuerySets y respuesta HTTP 404 para recursos fuera de la organización del usuario.
  - Adaptación de interfaces y botones condicionales mediante `perms`.
- **Clase 8 (CRUD Protegido con ModelForm, Modal y SweetAlert2):**
  - Vistas Basadas en Clases (`DeviceListView`, `DeviceCreateView`, `DeviceUpdateView`, `DeviceDeleteView`).
  - Reutilización de `DeviceForm` (`clean_name()`, unicidad case-insensitive, scoping en selectores de zona/categoría).
  - Modal Bootstrap 5 reutilizable para Crear y Editar (`_device_form_modal.html`) con persistencia de errores y reapertura automática (`open_modal=True`).
  - Confirmación interactiva de borrado mediante SweetAlert2 disparando formulario POST con CSRF.
  - Borrado lógico auditado marcando `deleted_at` sin pérdida física de registros.
- **Clase 9 (Archivos e Imágenes en Django):**
  - Campos opcionales `ImageField` y `FileField` en `Device`, con almacenamiento organizado por fecha.
  - Configuración `MEDIA_ROOT` / `MEDIA_URL`, servicio local solo con `DEBUG=True` y carpeta `media/` excluida de Git.
  - Carga multipart en el modal, validación de imagen, extensión PDF y límites de 2 MB para imágenes y 5 MB para manuales.
  - Presentación segura de imagen/manual cuando existen; Pillow declarado en `requirements.txt`.
- **Clase 10 (Búsqueda, Filtros, Orden y Paginación):**
  - Búsqueda `icontains` en nombre, serie, zona y categoría; filtros exactos por estado, zona y categoría.
  - Scoping organizacional aplicado antes de los parámetros GET, ordenamiento con whitelist y fallback seguro.
  - Paginación de 5, 15 o 30 filas, preferencia guardada en sesión y parámetros conservados al navegar.

### Material docente
- [Unidad 2 · Clase 9: Archivos e imágenes en Django](docs/clase9_archivos_imagenes_media.md)
- [Unidad 2 · Clase 10: Búsqueda, filtros, ordenamiento y paginación](docs/clase10_busqueda_filtros_paginacion.md)

---

### 🌐 Rutas Principales de la Aplicación
* **Inicio:** `http://127.0.0.1:8000/`
* **Catálogo y CRUD de Dispositivos:** `http://127.0.0.1:8000/dispositivos/`
* **Nuevo Dispositivo (Modal):** `http://127.0.0.1:8000/dispositivos/new/`
* **Iniciar Sesión:** `http://127.0.0.1:8000/accounts/login/`
* **Recuperar Contraseña:** `http://127.0.0.1:8000/password-reset/`
* **Panel de Administración:** `http://127.0.0.1:8000/admin/`

---

### 👥 Usuarios de Demostración y Pruebas
| Usuario | Rol | Contraseña | Organización |
| :--- | :--- | :--- | :--- |
| `admin` | Superusuario Global | `Admin123!` | Acceso Global |
| `admin_norte` | Admin Organizacional | `Password123!` | EcoEnergy Norte SpA |
| `operador_norte` | Operador | `Password123!` | EcoEnergy Norte SpA |
| `consulta_norte` | Consulta (Sólo Lectura) | `Password123!` | EcoEnergy Norte SpA |
| `admin_sur` | Admin Organizacional | `Password123!` | EcoEnergy Sur SpA |
| `operador_sur` | Operador | `Password123!` | EcoEnergy Sur SpA |
| `consulta_sur` | Consulta (Sólo Lectura) | `Password123!` | EcoEnergy Sur SpA |
| `staff_sin_perfil` | Staff sin perfil | `Password123!` | Denegación segura (sin datos) |

---

## 🧪 Ejecución de Pruebas Automatizadas

La suite incluye **50 pruebas automatizadas** que cubren modelos, admin, autenticación, sesiones, los 7 escenarios de recuperación de clave, permisos en vistas y el CRUD completo:

```bash
python manage.py test dispositivos
```

Resultado esperado:
```text
Ran 50 tests in ~1.6s
OK
```

