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

## 📌 Estado Actual y Próximos Pasos

El proyecto cuenta con modelos persistentes para organizaciones, departamentos, perfiles, categorías, zonas, dispositivos, mediciones, alertas y mantenimiento. Las vistas de catálogo y zonas consultan la base de datos y filtran por organización cuando el usuario autenticado posee un perfil.

## 🧰 Flujo de trabajo

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py check
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Admin: `http://127.0.0.1:8000/admin/`

Las credenciales y la configuración de base de datos se cargan desde `.env`. No se debe versionar ese archivo; usar `.env.example` como referencia.

## 🧪 Pruebas

```powershell
python manage.py test dispositivos
```

