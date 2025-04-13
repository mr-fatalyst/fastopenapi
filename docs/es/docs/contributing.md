# ¡Bienvenido!

Gracias por considerar contribuir a **FastOpenAPI** 🎉  
Esta guía explica cómo comenzar, realizar aportes, escribir commits, abrir pull requests y ejecutar pruebas.

---

## Configuración y ejecución

Instala las dependencias con:

```bash
# Fork the repo on GitHub first, then:
git clone https://github.com/yourusername/fastopenapi.git
cd fastopenapi
poetry install
```

Si no usas `poetry`, también puedes instalar manualmente:

```bash
pip install -e .[dev]
```

---

## Estructura del proyecto

- `fastopenapi/` — código principal de la biblioteca
- `examples/` — ejemplos para distintos frameworks
- `tests/` — pruebas unitarias
- `benchmarks/` — pruebas de rendimiento
- `docs/` — documentación en varios idiomas

---

## Ejecutar pruebas

Puedes ejecutar todas las pruebas con:

```bash
pytest
```

Incluye pruebas para la lógica central y la integración con los distintos frameworks soportados.

---

## Estilo de código

Herramientas utilizadas:

- `black` — formato automático
- `flake8` — análisis estático
- `isort` — orden de imports
- `pre-commit` — hooks de validación antes del commit

Instala los hooks:

```bash
pre-commit install
```

Ejecuta manualmente:

```bash
pre-commit run --all-files
```

---

## Git y Pull Requests

1. Haz un fork del repositorio
2. Crea una rama: `feature/tu-feature` o `fix/tu-arreglo`
3. Realiza commits pequeños y claros
4. Abre un PR describiendo:
   - Qué cambiaste o agregaste
   - Qué frameworks se ven afectados
   - Cómo lo probaste

---

## Documentación

Si modificas la API pública o el comportamiento, actualiza también la documentación:

- En `docs/en/`
- Opcional: traducciones en `docs/es/`, `docs/ru/`, etc.

---

## Comentarios y ayuda

¿No estás seguro de algo?  
Abre un issue o pregunta en el repositorio — ¡con gusto te ayudaremos!

