# FAQ (Preguntas Frecuentes)

Aquí encontrarás respuestas a preguntas comunes sobre FastOpenAPI. Si tienes otra duda, no dudes en abrir un issue en GitHub o contactarnos directamente.

---

#### **P: ¿Qué es FastOpenAPI y en qué se diferencia de FastAPI?**  
**R:** FastOpenAPI no es un framework web, sino una biblioteca que añade documentación OpenAPI/Swagger y validación de solicitudes/respuestas a frameworks ya existentes como Flask, AIOHTTP, etc. FastAPI, en cambio, es un framework completo que ya incluye esto de forma nativa.  
En resumen: si estás comenzando un nuevo proyecto, puedes usar FastAPI. Si ya tienes un proyecto o deseas usar otro framework, FastOpenAPI es ideal.

#### **P: ¿Qué frameworks son compatibles?**  
**R:** Actualmente, FastOpenAPI soporta:

- **AIOHTTP**
- **Falcon**
- **Flask**
- **Quart**
- **Sanic**
- **Starlette**
- **Tornado**

FastOpenAPI es modular y puede extenderse fácilmente. También puedes crear tu propio `Router` (ver sección "Uso avanzado").

#### **P: ¿Qué versiones de Python y Pydantic se requieren?**  
**R:** Python **3.10 o superior** y Pydantic **v2**. FastOpenAPI aprovecha las nuevas funciones de tipado de Python y la generación de esquemas JSON de Pydantic v2.

#### **P: ¿Cómo se documenta la autenticación (JWT, API Keys, etc.)?**  
**R:** FastOpenAPI no implementa autenticación directamente. Puedes definir manualmente `securitySchemes` dentro del esquema OpenAPI (ver "Uso avanzado"). Por ejemplo, puedes agregar un parámetro `token: str` en tus endpoints y validar el token con middleware o decoradores externos.

#### **P: ¿No funcionan /docs o /redoc?**  
**R:** Verifica que estás pasando correctamente la instancia `app` al inicializar el router:  
`router = FrameworkRouter(app=app)`  
Sin esto, no se registrarán las rutas de documentación. También asegúrate de que el servidor se esté ejecutando correctamente y que no haya prefijos de URL interfiriendo.

#### **P: ¿Se puede usar junto con otras bibliotecas como Flask-RESTx?**  
**R:** No es recomendable. Si usas varias herramientas que generan esquemas OpenAPI automáticamente, puede haber conflictos. FastOpenAPI está pensado como una solución independiente.

#### **P: ¿Tiene soporte para inyección de dependencias o tareas en segundo plano?**  
**R:** No directamente. FastOpenAPI se enfoca solo en documentación y validación. Estas funciones deben ser manejadas por el framework subyacente.

#### **P: ¿Es apto para producción?**  
**R:** FastOpenAPI está en desarrollo activo (versión pre-1.0), pero ya es estable para muchos casos. Se recomienda fijar la versión en `requirements.txt` y probar antes de cada despliegue.

#### **P: ¿Cómo puedo contribuir o reportar errores?**  
**R:** ¡Con gusto! Consulta la sección **Contribuir**. Puedes crear un issue o pull request en GitHub.

#### **P: ¿Hay proyectos de ejemplo que usen FastOpenAPI?**  
**R:** Sí, en la carpeta `examples/` del repositorio encontrarás ejemplos para cada framework compatible. Si usas FastOpenAPI en producción, ¡nos encantaría saberlo!

#### **P: ¿Qué versión de OpenAPI se genera?**  
**R:** FastOpenAPI genera OpenAPI 3.1.0, ya que Pydantic v2 produce esquemas JSON compatibles con esa versión.

---

¿Tienes más preguntas? Consulta también las secciones **Uso**, **Avanzado** o crea un issue en GitHub. ¡Tu retroalimentación nos ayuda a mejorar!
