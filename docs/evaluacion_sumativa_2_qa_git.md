# Evaluación Sumativa II - Registro de QA y Gestión Git

## 1. Control de calidad

Se realizó una verificación final de la configuración del proyecto mediante:

python manage.py check

Resultado:

System check identified no issues (0 silenced).

Posteriormente se ejecutó la suite completa de pruebas automatizadas:

python manage.py test dispositivos

La versión final evaluada contiene 26 pruebas automatizadas.

Resultado:

Ran 26 tests
OK

Esto confirma que todas las pruebas disponibles en la versión evaluada finalizaron satisfactoriamente.

---

## 2. Gestión de ramas

Durante la evaluación se verificó el uso de ramas de trabajo para las principales funcionalidades del proyecto.

Ramas identificadas:

- feature/modelos-auditoria-admin-basico
- feature/seguridad-scoping-admin
- feature/admin-pro-validaciones-seed
- docs/informe-evaluacion-sumativa-2

Las ramas funcionales fueron integradas a main mediante Pull Request:

- PR #1: feature/modelos-auditoria-admin-basico
- PR #2: feature/seguridad-scoping-admin
- PR #3: feature/admin-pro-validaciones-seed

La rama docs/informe-evaluacion-sumativa-2 corresponde al trabajo de documentación, pruebas y preparación del informe final.

---

## 3. Auditoría de archivos sensibles

Se comprobó mediante git ls-files que los siguientes archivos o directorios no se encuentran versionados:

- .env
- .venv/
- __pycache__/
- archivos .pyc

El repositorio también mantiene estas exclusiones mediante .gitignore.

---

## 4. Evidencias recopiladas

- Evidencia_Git_Final_01_Historial_Ramas_y_Merges.png
- Evidencia_Git_Final_02_Auditoria_Archivos_Sensibles.png
- Evidencia_QA_Final_01_Check_y_26_Tests.png

---

## 5. Hash de versión evaluada

El hash definitivo de main se registrará una vez que todas las ramas de trabajo y documentación hayan sido integradas.