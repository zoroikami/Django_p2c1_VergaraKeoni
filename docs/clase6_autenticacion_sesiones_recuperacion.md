# Unidad 2 · Clase 6: Autenticación, Sesiones y Desafío de Recuperación de Contraseña

## 🎯 Objetivo de Aprendizaje
Implementar un flujo completo de autenticación y manejo de sesiones para usuarios finales en EcoEnergy, fuera del Django Admin, junto al desafío de recuperación de contraseñas mediante códigos temporales seguros de 6 dígitos enviados por correo.

---

## 🔑 1. Autenticación y Manejo de Sesiones

### A. Configuración y Rutas
* **Rutas integradas:** `path('accounts/', include('django.contrib.auth.urls'))` en `config/urls.py`.
* **Destinos de redirección:**
  * `LOGIN_URL = 'login'`
  * `LOGIN_REDIRECT_URL = 'dispositivos:catalogo'`
  * `LOGOUT_REDIRECT_URL = 'login'`
* **Message Framework:** Mapeo de constantes de Django a estilos de Bootstrap 5 (`success`, `warning`, `danger`, `info`, `secondary`).

### B. Plantilla de Login (`templates/registration/login.html`)
* Hereda de `base.html` conservando el sistema de diseño visual de EcoEnergy.
* Formulario protegido con token `{% csrf_token %}`.
* Mensaje de error controlado y genérico: *"Usuario o contraseña incorrectos"*, evitando revelar si el fallo provino del nombre de usuario o de la contraseña.
* Enlace directo al flujo de recuperación de contraseña.

### C. Navegación Dinámica (`templates/base.html`)
* Si el usuario está autenticado:
  * Despliega nombre de usuario y empresa asociada (`request.user.profile.organization`).
  * Botón de cierre de sesión mediante **formulario POST con CSRF** hacia `{% url 'logout' %}` (conforme a los estándares modernos de seguridad de Django, evitando logouts por GET vulnerables a prefetch).
* Si el visitante es anónimo:
  * Presenta botón de acceso directo hacia `{% url 'login' %}`.
* Alertas globales de `messages` renderizadas dinámicamente con alertas descartables de Bootstrap 5.

### D. Sesión y Vistas Protegidas
* `request.session`: Utilizado para almacenar datos temporales de navegación, como contador de visitas (`inicio_visits`, `catalog_visits`) y trazabilidad del flujo de recuperación de contraseña.

---

## 🛡️ 2. Desafío: Recuperación de Contraseña con Código Temporal

### A. Modelo de Persistencia (`PasswordResetCode`)
* **`user`**: Clave foránea al usuario solicitante.
* **`code_hash`**: Almacenamiento seguro mediante algoritmo criptográfico con `make_password()` (el código **nunca** se almacena en texto plano en la base de datos).
* **`expires_at`**: Tiempo de vigencia estricto (TTL de 120 segundos configurable vía variable de entorno `PASSWORD_RESET_CODE_TTL_SECONDS`).
* **`is_used` / `used_at`**: Control de un solo uso; se marca como consumido inmediatamente al restablecer la contraseña.
* **`failed_attempts`**: Contador de intentos fallidos. Máximo permitido: 5 intentos antes de bloquear el código.

### B. Flujo de Tres Pasos
1. **`password-reset/` (Solicitud):**
   * Recibe correo del usuario.
   * **Seguridad contra enumeración:** Retorna siempre una respuesta genérica exitosa, impidiendo a atacantes descubrir qué correos están registrados en el sistema.
   * Si el usuario existe y está activo: invalida cualquier código previo, genera un código numérico seguro de 6 dígitos mediante el módulo `secrets` de Python, calcula la fecha de expiración y envía el correo.
2. **`password-reset/verify/` (Validación):**
   * Recibe el código de 6 dígitos.
   * Comprueba que exista solicitud activa, que no esté bloqueada por intentos ($\ge 5$), que no haya expirado ($< 120\text{ s}$) y verifica el hash mediante `check_password()`.
   * Si es incorrecto, incrementa `failed_attempts` y notifica intentos restantes.
   * Si es correcto, habilita la sesión para el cambio de clave.
3. **`password-reset/confirm/` (Actualización):**
   * Valida la nueva contraseña y su confirmación contra la suite completa de validadores de Django (`MinimumLengthValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`).
   * Aplica la nueva clave mediante `user.set_password()`, guarda el usuario, invalida el código (`is_used=True`) y redirige a `login` con mensaje de éxito.

### C. Configuración de Correo
* **Desarrollo inicial:** Salida a consola mediante `django.core.mail.backends.console.EmailBackend`.
* **Entornos de prueba y staging:** Conexión SMTP a Mailtrap configurada mediante variables en `.env` (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`).

---

## 📋 3. Matriz de Pruebas Automatizadas (7 Escenarios Requeridos)

| # | Escenario Evaluado | Resultado Verificado | Estado |
| :-: | :--- | :--- | :-: |
| **1** | Código correcto ingresado antes de 120 s | Autoriza paso a confirmación de contraseña | ✅ Aprobado |
| **2** | Código incorrecto | Rechaza operación e incrementa intentos fallidos | ✅ Aprobado |
| **3** | Código correcto ingresado después de 120 s | Rechaza la operación por código expirado | ✅ Aprobado |
| **4** | Código ya utilizado previamente | Impide reutilización y solicita nuevo código | ✅ Aprobado |
| **5** | Solicitud de nuevo código | Invalida automáticamente los códigos anteriores | ✅ Aprobado |
| **6** | Solicitud con correo inexistente | Respuesta visual genérica sin filtrar datos internos | ✅ Aprobado |
| **7** | Actualización exitosa de contraseña | Permite login con nueva clave; clave anterior queda anulada | ✅ Aprobado |

---

## ❓ 4. Preguntas de Cierre Técnicas (Defensa de la Clase 6)

1. **¿Por qué no conviene almacenar el código temporal en texto plano?**
   * Si la base de datos o sus respaldos sufren una filtración, un atacante con acceso a códigos en texto plano podría secuestrar cuentas de inmediato. Almacenar el hash (`make_password`) garantiza confidencialidad incluso ante incidentes de volcado de datos.
2. **¿Qué diferencia existe entre "código incorrecto" y "código expirado"?**
   * Un *código incorrecto* indica un error de digitación o un intento de fuerza bruta (lo cual amerita incrementar el contador de intentos fallidos y bloquear el acceso). Un *código expirado* indica que se superó la ventana temporal segura (120 s), requiriendo generar un nuevo desafío.
3. **¿Por qué la aplicación no debería decir "ese correo no existe"?**
   * Responder que un correo no existe permite a atacantes realizar *user enumeration* (mapeo de cuentas válidas dentro de la organización). Un mensaje neutro y genérico protege la privacidad de los usuarios.
