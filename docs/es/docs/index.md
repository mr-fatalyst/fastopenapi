# FastOpenAPI

<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Logo">
</p>

<p align="center">
  <b>FastOpenAPI</b> es una biblioteca para generar e integrar esquemas OpenAPI usando Pydantic y varios frameworks.
</p>

<p align="center">
  Este proyecto fue inspirado por <a href="https://fastapi.tiangolo.com/">FastAPI</a> y busca ofrecer una experiencia amigable para desarrolladores similar.
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/mr-fatalyst/fastopenapi">
  <img src="https://github.com/mr-fatalyst/fastopenapi/actions/workflows/master.yml/badge.svg">
  <img src="https://codecov.io/gh/mr-fatalyst/fastopenapi/branch/master/graph/badge.svg?token=USHR1I0CJB">
  <img src="https://img.shields.io/pypi/v/fastopenapi">
  <img src="https://img.shields.io/pypi/pyversions/fastopenapi">
  <img src="https://static.pepy.tech/badge/fastopenapi" alt="PyPI Downloads">
</p>

---

## Sobre el proyecto

**FastOpenAPI** es una biblioteca de Python para generar e integrar esquemas OpenAPI usando modelos Pydantic en diversos frameworks web. Inspirada por FastAPI, proporciona una experiencia similar, pero compatible con frameworks como AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, Tornado y Django.
Con FastOpenAPI puedes añadir documentación interactiva y validación automática a proyectos existentes sin cambiar de framework.

FastOpenAPI aún está en desarrollo activo (versión pre-1.0), pero ya se encuentra estable para muchos usos. Todos los aportes y comentarios son bienvenidos.

## Características

- **Generación automática de OpenAPI** – define tus rutas y modelos, y FastOpenAPI generará el esquema completo.
- **Soporte para Pydantic v2** – validación y serialización robusta para entradas y salidas.
- **Compatibilidad con múltiples frameworks** – incluyendo AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, Tornado y Django.
- **Estilo de ruteo similar a FastAPI** – decoradores como `@router.get`, `@router.post`, etc.
- **Documentación interactiva integrada** – Swagger UI (`/docs`) y ReDoc (`/redoc`).
- **Validación y gestión de errores** – respuestas automáticas ante entradas inválidas, con clases como `BadRequestError`, `ResourceNotFoundError`.

Explora la documentación usando el menú lateral. Comienza con **Instalación** y **Inicio Rápido**, continúa con **Uso**. Cada framework compatible tiene su propia página. Para temas más avanzados, revisa **Uso Avanzado** y la **Referencia API**.  
Si deseas contribuir, visita la sección **Contribuir**. Cambios importantes están en el **Changelog**, y también puedes revisar la sección de **FAQ**.

