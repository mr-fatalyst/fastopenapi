# Erweiterte Nutzung

In diesem Abschnitt behandeln wir fortgeschrittene Themen wie die Architektur von FastOpenAPI, die Erweiterung auf neue Frameworks und die Anpassung des generierten Verhaltens oder der Dokumentation. Diese Informationen richten sich an Entwickler:innen, die FastOpenAPI tiefer verstehen, anpassen oder in nicht-standardisierte Umgebungen integrieren möchten.

## Architekturüberblick

Das Design von FastOpenAPI ist von FastAPI inspiriert, aber framework-unabhängig aufgebaut. Die Hauptkomponenten sind:

- **BaseRouter**: Die zentrale Basisklasse, welche Routing, OpenAPI-Schema-Generierung und Verarbeitung von Requests/Responses kapselt. Sie ist nicht an ein spezifisches Framework gebunden.
- **Framework-spezifische Router**: Subklassen von `BaseRouter`, z. B. `FlaskRouter`, `StarletteRouter` usw., die die Integration mit konkreten Frameworks übernehmen.
- **Pydantic-Modelle**: FastOpenAPI nutzt Pydantic zur Definition, Validierung und Dokumentation von Datenstrukturen.
- **OpenAPI-Generierung**: FastOpenAPI erstellt auf Basis von Metadaten (Routen, Parameter, Modelle) automatisch ein vollständiges OpenAPI-3.1-Schema. Dieses ist unter `/openapi.json` abrufbar.
- **Dokumentationsrouten**: Über `/docs` (Swagger UI) und `/redoc` (ReDoc) stehen interaktive Dokumentationen zur Verfügung.

## Ablauf eines Requests

1. Eine Anfrage trifft auf die Route einer Anwendung (z. B. in Flask), die mit FastOpenAPI registriert wurde.
2. Der Dekorator `@router.get/post/...` hat die Funktion registriert.
3. Vor dem Funktionsaufruf führt FastOpenAPI:
   - Extraktion von Pfadparametern (meist durch das Framework selbst),
   - Validierung von Query-/Header-/Body-Parametern (via Pydantic),
   - Fehlerbehandlung bei ungültigen Eingaben durch.
4. Die Funktion wird mit validierten Parametern aufgerufen.
5. Die Antwort wird je nach `response_model` serialisiert (validiert und in JSON umgewandelt).
6. Im Fehlerfall (z. B. `ResourceNotFoundError`) wird eine JSON-Fehlermeldung erzeugt.
7. Die Antwort wird durch das Framework zurückgegeben.

## Erweiterung auf weitere Frameworks

FastOpenAPI ist modular konzipiert. Wenn dein Framework nicht unterstützt wird, kannst du eine eigene Integration schreiben.

### Vorgehen:

- Erstelle eine neue Klasse, die `BaseRouter` erweitert.
- Implementiere:
  - Registrierung von Routen (z. B. `add_route()`),
  - (Optional) Startlogik der App,
  - Einbindung von `/docs`, `/redoc`, `/openapi.json`.

### Hinweise:

- Bestehende Implementierungen wie `FlaskRouter`, `StarletteRouter` etc. dienen als gute Vorlage.
- Methoden wie `get_openapi_schema()` in `BaseRouter` sind wiederverwendbar.

## Beispiel: Eigener Router

Wenn du z. B. einen `MyCustomFrameworkRouter` erstellen willst:

```python
from fastopenapi.base_router import BaseRouter

class MyCustomRouter(BaseRouter):
    def add_route(self, path, method, handler):
        # Framework-spezifische Logik
        pass
```

Du kannst bestehende Methoden überschreiben oder Hooks hinzufügen.

---

