# Django_p2c1_VergaraKeoni - Clase 4: Templates, Herencia y Contexto

Proyecto Django que implementa separación de responsabilidades usando vistas, contextos y plantillas HTML con herencia y navegación por nombres de URL.

---

## 📁 Estructura del Proyecto

```text
Django_p2c1_VergaraKeoni/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── dispositivos/
│   ├── urls.py
│   ├── views.py
│   └── ...
├── templates/
│   ├── base.html
│   └── dispositivos/
│       ├── inicio.html
│       └── catalogo.html
├── manage.py
└── README.md
```

---

## 📄 Templates y Herencia

- **Plantilla base**: `templates/base.html`
  - Define la estructura HTML compartida (`<!doctype html>`, `<head>`, `<nav>`, `<main>`).
  - Incluye bloques reutilizables `{% block title %}` y `{% block content %}`.
  - Maneja la barra de navegación usando `{% url 'dispositivos:inicio' %}` y `{% url 'dispositivos:catalogo' %}`.

- **Plantillas hijas**:
  - `templates/dispositivos/inicio.html`: Hereda de `base.html` mediante `{% extends "base.html" %}` e inyecta la información del sistema.
  - `templates/dispositivos/catalogo.html`: Hereda de `base.html` y recorre la colección de dispositivos con `{% for %}` y `{% empty %}`.

---

## 🌐 Rutas Funcionales

| Ruta | Nombre de URL (`name`) | Vista | Descripción |
|---|---|---|---|
| `/` | `dispositivos:inicio` | `dispositivos.views.inicio` | Página de bienvenida con datos del sistema. |
| `/dispositivos/` | `dispositivos:catalogo` | `dispositivos.views.catalogo` | Catálogo con listado de dispositivos registrados. |

---

## 🔑 Claves de Contexto

### 1. Vista `inicio` (`/`)
- `sistema`: Nombre del sistema (`"EcoEnergy"`).
- `mensaje`: Descripción del servicio (`"Monitoreo energético responsable"`).
- `asignatura`: Nombre del curso (`"Programación Back End"`).

### 2. Vista `catalogo` (`/dispositivos/`)
- `dispositivos`: Lista de diccionarios con los dispositivos (cada uno con `nombre` y `estado`).

---

## 🚀 Ejecución y Pruebas

### 1. Verificar configuración del proyecto
```bash
python manage.py check
```

### 2. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```

### 3. Prueba de navegación
- Ingresar a `http://127.0.0.1:8000/` para ver la página de inicio.
- Hacer clic en el enlace **Dispositivos** del menú de navegación para acceder a `http://127.0.0.1:8000/dispositivos/`.
- Hacer clic en el enlace **Inicio** para volver a la página inicial.
