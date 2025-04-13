# Installation

FastOpenAPI ist auf PyPI verfügbar und unterstützt **Python 3.10+**. Du kannst entweder nur die Kernbibliothek oder optionale Abhängigkeiten für bestimmte Webframeworks installieren.

## Voraussetzungen

- **Python 3.10 oder höher** – erforderlich wegen moderner Typisierung und Unterstützung für Pydantic v2.
- (Optional) Ein bestehendes Webframework (wie Flask, Starlette usw.), falls du eines integrieren möchtest. Falls noch nicht installiert, kannst du es über die entsprechenden Extras automatisch mitinstallieren.

## Installation via pip

#### Nur FastOpenAPI installieren  
*Standardinstallation*
```bash
pip install fastopenapi
```

#### FastOpenAPI mit spezifischem Framework installieren  
*Nützlich für neue Projekte ohne vorinstalliertes Framework*
```bash
pip install fastopenapi[aiohttp]
```
```bash
pip install fastopenapi[falcon]
```
```bash
pip install fastopenapi[flask]
```
```bash
pip install fastopenapi[quart]
```
```bash
pip install fastopenapi[sanic]
```
```bash
pip install fastopenapi[starlette]
```
```bash
pip install fastopenapi[tornado]
```

---
