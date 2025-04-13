# Uso Avanzado

En esta sección se presentan temas avanzados como la arquitectura interna de FastOpenAPI, cómo extenderlo a nuevos frameworks y cómo personalizar la generación de esquemas o el comportamiento predeterminado. Está pensada para desarrolladores que deseen una integración profunda o crear adaptadores personalizados.

## Arquitectura

FastOpenAPI se inspira en FastAPI pero está diseñado para ser independiente del framework. Sus componentes clave son:

- **BaseRouter**: Clase base abstracta que maneja enrutamiento, generación de esquemas y validación. No depende de ningún framework específico.
- **Routers por framework**: Subclases de `BaseRouter` que implementan lógica específica para cada framework, como `FlaskRouter`, `StarletteRouter`, etc.
- **Modelos Pydantic**: Definen y validan datos de entrada/salida.
- **Generación OpenAPI**: Se basa en las rutas, modelos y metadatos definidos por el usuario.
- **Documentación automática**: Se crean rutas `/docs`, `/redoc` y `/openapi.json`.

## Flujo de una solicitud

1. Una petición llega a una ruta definida con FastOpenAPI.
2. El decorador `@router.get`, `@router.post`, etc. ha registrado una función.
3. Antes de invocar esa función:
   - Se extraen los parámetros de ruta.
   - Se validan parámetros de query/header/body usando Pydantic.
   - Si hay errores, se lanza una respuesta automática con código 400 o 422.
4. La función se ejecuta con parámetros ya validados.
5. La respuesta se valida con `response_model` y se convierte a JSON.
6. Si se lanza una excepción como `ResourceNotFoundError`, se devuelve una respuesta estructurada con código 404.

## Crear tu propio adaptador (router)

Puedes extender FastOpenAPI a cualquier framework escribiendo una subclase de `BaseRouter`.

### Pasos

- Crea una nueva clase que herede de `BaseRouter`.
- Implementa métodos como:
  - `add_route()` para registrar endpoints.
  - `include_router()` si aplica.
  - Lógica para registrar `/docs`, `/redoc`, `/openapi.json`.

### Ejemplo

```python
from fastopenapi.base_router import BaseRouter

class MyCustomRouter(BaseRouter):
    def add_route(self, path, method, handler):
        # Aquí va la lógica del framework
        pass
```

### Referencias útiles

Consulta los archivos:
- `routers/flask.py`
- `routers/starlette.py`
- `base_router.py`

Allí verás cómo se integran los métodos comunes y cómo cada router traduce el comportamiento a su framework subyacente.

---

FastOpenAPI está diseñado para que sea fácil agregar soporte para más frameworks o entornos personalizados (microservicios internos, CLI, RPC, etc.).
