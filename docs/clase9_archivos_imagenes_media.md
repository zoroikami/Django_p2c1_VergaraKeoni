# Unidad 2 · Clase 9: Archivos e imágenes en Django

## Objetivo
Incorporar imagen y manual PDF al CRUD protegido de `Device`, almacenando los archivos en el storage y su referencia en la base de datos.

## Implementación

- `Device.image` usa `ImageField` y `upload_to="devices/images/%Y/%m/"`. Django valida que el contenido sea una imagen y Pillow proporciona el soporte requerido.
- `Device.manual` usa `FileField` en `devices/manuals/%Y/%m/`, con `FileExtensionValidator` para permitir la extensión PDF.
- Ambos campos son opcionales. `DeviceForm` limita la imagen a 2 MB y el manual a 5 MB. El atributo HTML `accept` solo orienta el selector del navegador; la validación se realiza en el servidor.
- El modal reutilizable envía `multipart/form-data`. Las vistas genéricas `CreateView` y `UpdateView` enlazan automáticamente los archivos con el `ModelForm`.
- `MEDIA_ROOT` apunta al directorio local `media/`, y `MEDIA_URL` usa `/media/`. `config/urls.py` publica esos archivos solo durante el desarrollo con `DEBUG=True`.
- La tabla comprueba cada campo antes de usar `.url`, muestra texto alternativo para imágenes y ofrece un enlace al manual cuando está disponible.

## Seguridad y ciclo de vida

`FileExtensionValidator` no demuestra que el contenido sea un PDF confiable. Los manuales se exponen mediante MEDIA en desarrollo, por lo que no se deben subir documentos sensibles; en producción se requiere storage y autorización adecuados. Los archivos antiguos no se borran automáticamente al reemplazar o archivar un dispositivo, así que la política actual es conservarlos y considerar esa limpieza explícitamente antes de automatizarla.

La carpeta `media/` está excluida de Git. Pillow y los dos campos están declarados en `requirements.txt` y en la migración `0006_device_image_device_manual`.

## Verificación

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test dispositivos.tests.Clase9FilesAndClase10ListControlsTest
```

Las pruebas verifican carga y persistencia, extensión no permitida y límite de tamaño.
