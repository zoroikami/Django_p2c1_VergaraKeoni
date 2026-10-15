# Unidad 2 · Clase 10: Búsqueda, filtros, ordenamiento y paginación

## Objetivo
Convertir el catálogo CRUD existente en un listado consultable sin perder permisos ni el aislamiento por organización.

## Flujo de consulta

`DeviceListView.get_queryset()` construye la consulta en este orden:

1. Scoping: superusuarios ven dispositivos activos de todas las organizaciones; el resto solo los de su perfil. Los dispositivos archivados quedan excluidos.
2. Búsqueda opcional con `Q` e `icontains` sobre nombre, número de serie, zona y categoría.
3. Filtros exactos opcionales por estado, zona y categoría. Los selectores de zona también respetan la organización del usuario.
4. Orden ascendente/descendente desde `ORDERING_MAP`; cualquier alias no permitido vuelve a nombre ascendente. La clave primaria desempata de forma estable.
5. `ListView` pagina el resultado final.

Los controles usan GET y permiten combinar `q`, `status`, `zone`, `category`, `order` y `page_size`. El enlace para limpiar filtros vuelve al catálogo sin parámetros.

## Paginación y sesión

`get_paginate_by()` solo acepta 5, 15 o 30 registros. La selección se guarda en `request.session["device_page_size"]`, con 15 como valor inicial; una entrada inválida no reemplaza la preferencia previa. El contexto crea `query_params` sin `page`, y los enlaces anterior/siguiente conservan los demás parámetros. Los contadores del encabezado reflejan el resultado filtrado completo, no solo la página visible.

## Verificación

```powershell
python manage.py test dispositivos.tests.Clase9FilesAndClase10ListControlsTest
python manage.py test dispositivos.tests.Clase8ProtectedCrudModelFormAndSwalTest
```

Las pruebas comprueban filtros combinados, aislamiento entre Norte y Sur, fallback de orden, whitelist de tamaños y conservación de la consulta entre páginas.
