# FastOpenAPI

<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Logo">
</p>

<p align="center">
  <b>FastOpenAPI</b> is a library for generating and integrating OpenAPI schemas using Pydantic and various frameworks.
</p>

<p align="center">
  This project was inspired by <a href="https://fastapi.tiangolo.com/">FastAPI</a> and aims to provide a similar developer-friendly experience.
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

## About

**FastOpenAPI** is a Python library for seamlessly generating and integrating OpenAPI schemas using Pydantic models across multiple web frameworks. Inspired by FastAPI, it aims to provide a similar developer-friendly experience for frameworks like AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, and Tornado. With FastOpenAPI, you can add interactive API documentation and request/response validation to your existing web application without switching frameworks.

FastOpenAPI is currently in active development (pre-1.0). While it's already usable, expect potential breaking changes as the project evolves. We welcome feedback and contributions to improve stability and add new features.

## Features

- **Auto-generated OpenAPI schemas** – Define your API routes and data models, and FastOpenAPI will automatically generate a complete OpenAPI (Swagger) schema.
- **Pydantic v2 support** – Leverage Pydantic models for data validation and serialization. Both request payloads and responses can be validated with Pydantic, ensuring correct data types.
- **Multi-framework integration** – Includes out-of-the-box support for AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, and Tornado. This lets you use FastOpenAPI with your preferred web framework seamlessly.
- **FastAPI-style routing** – Use decorator-based routing (e.g. `@router.get`, `@router.post`) similar to FastAPI’s `APIRouter`. This proxy routing provides a familiar interface for defining endpoints and automatically ties into the framework’s routing.
- **Interactive docs UIs** – Automatically serves Swagger UI at `/docs` and ReDoc at `/redoc` in your application for interactive API exploration and documentation.
- **Request validation and error handling** – Invalid inputs are caught and returned as HTTP errors with JSON error messages. Custom exception classes are provided for common API errors (400 Bad Request, 404 Not Found, etc.) to simplify error handling.

Use the navigation to explore the documentation. Start with **Installation** and **Quickstart** to get **FastOpenAPI** up and running, then see **Usage** for deeper examples. Framework-specific guides provide instructions for each supported framework. For advanced topics (like extending FastOpenAPI or understanding its architecture), check out **Advanced Usage** and the **API Reference**. If you want to contribute or see what’s changed in each release, see the **Contributing** and **Changelog** sections. Finally, our **FAQ** addresses common questions.
