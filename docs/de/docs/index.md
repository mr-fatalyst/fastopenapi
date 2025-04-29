# FastOpenAPI

<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Logo">
</p>

<p align="center">
  <b>FastOpenAPI</b> ist eine Bibliothek zur Generierung und Integration von OpenAPI-Schemas mit Pydantic und verschiedenen Frameworks.
</p>

<p align="center">
  Dieses Projekt wurde von <a href="https://fastapi.tiangolo.com/">FastAPI</a> inspiriert und zielt darauf ab, eine ähnlich entwicklerfreundliche Erfahrung zu bieten.
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

## Über das Projekt

**FastOpenAPI** ist eine Python-Bibliothek zur Generierung und Integration von OpenAPI-Schemas mithilfe von Pydantic-Modellen in verschiedenen Webframeworks. Inspiriert von FastAPI bietet sie eine vergleichbare Entwicklererfahrung – aber für Frameworks wie AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, Tornado und Django. Mit FastOpenAPI kannst du interaktive API-Dokumentation und automatische Validierung zu bestehenden Projekten hinzufügen, ohne das Framework wechseln zu müssen.

FastOpenAPI befindet sich derzeit in aktiver Entwicklung (noch vor Version 1.0). Die Bibliothek ist schon jetzt einsatzfähig, aber Änderungen sind möglich. Feedback und Beiträge sind sehr willkommen.

## Merkmale

- **Automatische OpenAPI-Generierung** – definiere deine Routen und Modelle, FastOpenAPI erstellt automatisch eine vollständige OpenAPI-Spezifikation.
- **Unterstützung für Pydantic v2** – nutzt Pydantic zur Validierung und Serialisierung von Daten, sowohl für Anfragen als auch für Antworten.
- **Multi-Framework-Unterstützung** – unterstützt AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, Tornado und Django.
- **FastAPI-ähnlicher Routing-Stil** – verwende `@router.get`, `@router.post` etc., ähnlich wie bei FastAPI.
- **Interaktive Dokumentation** – Swagger UI (`/docs`) und ReDoc (`/redoc`) sind direkt integriert.
- **Fehlerbehandlung und Validierung** – bei ungültigen Daten wird ein JSON-Fehler zurückgegeben. Enthält Standardfehlerklassen für 400, 404 usw.

Verwende die Navigation auf der linken Seite, um die Dokumentation zu erkunden. Beginne mit den Abschnitten **Installation** und **Schnellstart**, und fahre fort mit **Verwendung**. Für jedes unterstützte Framework gibt es eine eigene Seite. Fortgeschrittene Themen findest du unter **Erweiterte Nutzung** und **API-Referenz**. Wenn du mithelfen möchtest, schau unter **Mitwirken**. Änderungen findest du im **Changelog**, häufige Fragen unter **FAQ**.
