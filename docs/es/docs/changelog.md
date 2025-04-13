# Registro de Cambios (Changelog)

Todos los cambios importantes en FastOpenAPI se documentan en este archivo.

## [0.5.0] – 2025-04-13

### Añadido
- **AioHttpRouter** para integración con el framework AIOHTTP (soporte async).
- Caché a nivel de clase para los esquemas de modelos Pydantic (mejora el rendimiento al evitar la regeneración del mismo esquema).
- Parámetro `response_errors` en los decoradores de rutas para documentar errores en OpenAPI.
- Módulo `error_handler` para respuestas de error estándar (incluye clases como `BadRequestError`, `ResourceNotFoundError`).
- Soporte de tipos simples (`int`, `float`, `bool`, `str`) como `response_model`.

## [0.4.0] – 20/03/2025

### Añadido
- Soporte para **ReDoc UI** (disponible en `/redoc`).
- **TornadoRouter** para el framework Tornado.

### Cambios
- Reescritura de tests para mejorar cobertura y fiabilidad.

### Corregido
- Códigos de error internos cambiados de 422 a 500, conforme a los estándares HTTP.

### Eliminado
- Métodos `add_docs_route` y `add_openapi_route` de `BaseRouter` (las rutas ahora se añaden automáticamente).

## [0.3.1] – 15/03/2025

### Corregido
- Fallo al importar routers sin tener instalado el framework (ahora se captura `ModuleNotFoundError`).

## [0.3.0] – 15/03/2025

### Añadido
- **QuartRouter** para el framework Quart (async).
- Primera versión de la documentación (introducción y ejemplos).

### Cambios
- Mejorado el import: ahora puedes hacer `from fastopenapi.routers import YourRouter`.

### Corregido
- Soporte correcto de query parameters como modelos en métodos GET.

## [0.2.1] – 12/03/2025

### Corregido
- Serialización de respuesta: `_serialize_response` ahora convierte modelos a dict antes de convertir a JSON.
- Corrección de errores cuando el `DataLoader` devolvía datos vacíos.
- Se añadieron tests para cubrir estos casos.
- Este archivo `CHANGELOG.md` fue añadido.

## [0.2.0] – 11/03/2025

### Añadido
- Función `resolve_endpoint_params` en `BaseRouter` para manejo de parámetros de path/query/body.
- Soporte para `prefix` en `include_router` para agrupar rutas.
- Soporte para `status_code` en decoradores.

### Cambios
- Refactor de routers existentes para mayor uniformidad y reducción de duplicación.

### Eliminado
- Eliminado `register_routes` en la implementación de Starlette (reemplazado por refactor).

## [0.1.0] – 01/03/2025

### Añadido
- Publicación inicial de FastOpenAPI.
- Funcionalidad básica:
  - Ruteo base
  - Soporte para Falcon, Flask, Sanic, Starlette
  - Generación de OpenAPI mediante Pydantic v2
  - Validación de parámetros y cuerpos
- README y ejemplos básicos
- Tests iniciales para rutas y esquemas
