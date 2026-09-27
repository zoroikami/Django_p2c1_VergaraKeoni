# EcoEnergy - Sistema de Monitoreo Energético Responsable

Proyecto Back End desarrollado con **Python** y **Django** para la asignatura **Programación Back End**.

---

## 🎯 Descripción y Objetivo

**EcoEnergy** es una aplicación web orientada al monitoreo energético responsable y a la visualización de dispositivos de control. Su objetivo actual es implementar una arquitectura desacoplada mediante el uso de vistas (`views.py`), contextos de datos y plantillas HTML (`templates`) con herencia (`base.html`) y navegación basada en nombres de rutas.

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
  source .venv/Scripts/activate   # o source .venv/bin/activate
  ```

### 3. Instalación de Dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

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
├── dispositivos/
│   ├── apps.py
│   ├── urls.py           # Rutas locales (app_name = "dispositivos")
│   └── views.py          # Lógica de vistas y preparación de contextos
├── templates/
│   ├── base.html         # Plantilla base con navegación y bloques compartidos
│   └── dispositivos/
│       ├── inicio.html   # Plantilla hija con contexto de bienvenida
│       └── catalogo.html # Plantilla hija con iteración de colección de datos
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

## 🧰 Flujo de Puesta en Marcha

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py check
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

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

```powershell
python manage.py test dispositivos
```

