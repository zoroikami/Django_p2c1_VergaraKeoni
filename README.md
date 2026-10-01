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

## 📌 Estado Actual del Proyecto (Unidad 2 Completa)

El proyecto cuenta con la implementación completa de las 5 clases de la **Unidad 2**:
- **Clase 1 (Modelo de Datos y Arquitectura):** Modelos de negocio con `BaseModel` abstracto (`created_at`, `updated_at`, `deleted_at`) y diseño modular.
- **Clase 2 (Modelos y Migraciones):** Soporte multi-motor (SQLite/MySQL) vía `.env`, constraints de unicidad, índices y migraciones aplicadas.
- **Clase 3 (Django Admin Básico):** Administración con `list_display`, `search_fields` cruzando relaciones, `list_filter`, `list_select_related`, `date_hierarchy` y representaciones `__str__` legibles.
- **Clase 4 (Usuarios, Perfiles y Roles):** Integración `User + UserProfile` con validación organizacional en `clean()`, y roles con grupos (`Administrador Organizacional`, `Operador`, `Consulta`) bajo el principio de menor privilegio.
- **Clase 5 (Seguridad en Admin y Scoping):** Aislamiento multi-tenant con `get_queryset` acotado por organización, exclusión de borrado lógico, `formfield_for_foreignkey` restrictivo, auto-asignación en `save_model`, permisos por objeto (`has_change_permission`), acción de archivado y `DepartmentInline`.

Panel de Administración: `http://127.0.0.1:8000/admin/`

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

## 🧪 Ejecución de Pruebas Automatizadas

```bash
python manage.py test dispositivos
```

## Demostración de Admin Pro

1. Ingresar como `admin_norte`. En **Organizations**, abrir **EcoEnergy Norte**. La tabla **Departments** permite agregar o editar departamentos en el mismo formulario; guardar con **Save**. El rol Administrador Organizacional puede cambiar solo su propia organización.
2. Como `admin_norte`, abrir **Devices**, seleccionar un dispositivo activo de Norte y ejecutar **Archivar dispositivos seleccionados**. Aparece un mensaje con la cantidad archivada. El registro conserva su fila en la base con `deleted_at` y deja de aparecer en la lista de ese usuario. La eliminación física está deshabilitada en el Admin.
3. Para mostrar la validación, entrar como `admin`, abrir **Devices → Add device**, elegir **EcoEnergy Norte** como organización y una zona de **EcoEnergy Sur**; completar los demás campos y pulsar **Save**. El formulario marca **Zone** con el mensaje «La zona debe pertenecer a la misma organización que el dispositivo». También se puede probar en **User profiles** asignando a un perfil de Norte un departamento de Sur.
4. Para evidenciar el borrado lógico precargado, entrar como `admin` y buscar `SN-NTE-ARCH-001` en **Devices**; su campo `deleted_at` contiene la fecha de archivo. Como `operador_norte` o `consulta_norte`, la lista solo muestra datos propios y activos.

Para el informe, capturar la vista de la organización con el Inline, la lista de dispositivos inmediatamente después de archivar con el mensaje de éxito y el formulario de dispositivo con el error de zona visible.
