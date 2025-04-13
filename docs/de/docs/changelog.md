# Changelog

Alle bedeutenden Änderungen an FastOpenAPI werden in dieser Datei dokumentiert.

## [0.5.0] – Unveröffentlicht

### Hinzugefügt
- **AioHttpRouter** zur Integration mit dem AIOHTTP-Framework (async-Unterstützung).
- Klassencache für Pydantic-Model-Schemas zur Leistungsverbesserung (vermeidet wiederholte Generierung von JSON Schema).
- `response_errors`-Parameter für Routen-Dekoratoren, um Fehlerrückgaben in OpenAPI zu dokumentieren.
- Modul `error_handler` für standardisierte Fehlerantworten (stellt Fehlerklassen wie `BadRequestError`, `ResourceNotFoundError` usw. bereit).
- Unterstützung einfacher Python-Typen (`int`, `float`, `bool`, `str`) als `response_model`.

## [0.4.0] – 20.03.2025

### Hinzugefügt
- Unterstützung für **ReDoc UI** (verfügbar unter `/redoc`).
- **TornadoRouter** für das Tornado-Framework.

### Geändert
- Alle Tests überarbeitet zur Verbesserung der Abdeckung und Zuverlässigkeit.

### Behoben
- Fehlercode bei internen Fehlern geändert: von 422 auf 500, gemäß HTTP-Standards.

### Entfernt
- `add_docs_route` und `add_openapi_route` Methoden aus `BaseRouter` entfernt – Dokumentationsrouten werden jetzt automatisch hinzugefügt.

## [0.3.1] – 15.03.2025

### Behoben
- Fehler beim Import von Routern ohne installiertes Framework (Abfangen von `ModuleNotFoundError`).

## [0.3.0] – 15.03.2025

### Hinzugefügt
- **QuartRouter** für das Quart-Framework (async).
- Erste Dokumentation (Einführung und Grundbeispiele) im Repository.

### Geändert
- Vereinfachter Import: jetzt `from fastopenapi.routers import YourRouter`.

### Behoben
- Query-Parameter über Pydantic-Modelle in GET-Routen werden nun korrekt erkannt und genutzt.

## [0.2.1] – 12.03.2025

### Behoben
- Serialisierung von Antworten: `_serialize_response` konvertiert BaseModel jetzt korrekt in ein dict vor JSON.
- Fehler im `DataLoader` bei leeren Daten beseitigt.
- Zusätzliche Tests für obige Fälle hinzugefügt.
- Diese Changelog-Datei (`CHANGELOG.md`) hinzugefügt.

## [0.2.0] – 11.03.2025

### Hinzugefügt
- `resolve_endpoint_params` in `BaseRouter` implementiert zur Parameterauswertung (path, query, body).
- `prefix`-Support in `include_router` zur Gruppierung von Routen.
- `status_code`-Support in Dekoratoren (Default-Statuscode setzen).

### Geändert
- Refactoring aller Router-Implementierungen zur Vereinheitlichung und Reduzierung von Redundanz.

### Entfernt
- `register_routes` aus Starlette-Implementierung entfernt (veraltet durch Refactoring).

## [0.1.0] – 01.03.2025

### Hinzugefügt
- Erste Veröffentlichung von FastOpenAPI.
- Grundfunktionalität implementiert:
  - Basisrouter-Klassen
  - Unterstützung für Falcon, Flask, Sanic, Starlette
  - OpenAPI-Schema-Generierung über Pydantic v2
  - Parameter- und Body-Validierung
- README und einfache Beispiele hinzugefügt.
- Erste Tests zur Schema-Generierung und Routenregistrierung integriert.
