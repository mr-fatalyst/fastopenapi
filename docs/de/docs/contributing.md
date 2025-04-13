# Willkommen!

Vielen Dank, dass du zur Entwicklung von **FastOpenAPI** beitragen möchtest 🎉  
Dieses Dokument erklärt, wie du loslegen kannst, Beiträge leistest, Commits erstellst, Pull Requests einreichst und Tests ausführst.

---

## Einrichtung & Ausführung

Installiere Abhängigkeiten mit:

```bash
git clone https://github.com/yourusername/fastopenapi.git
cd fastopenapi
poetry install
```

Wenn du kein `poetry` verwendest, kannst du manuell installieren:

```bash
pip install -e .[dev]
```

---

## Projektstruktur

- `fastopenapi/` — Hauptbibliothek
- `examples/` — Beispiele für verschiedene Frameworks
- `tests/` — Testfälle für jedes unterstützte Framework
- `benchmarks/` — Performance-Tests
- `docs/` — Dokumentation in mehreren Sprachen

---

## Tests ausführen

Starte die Tests mit:

```bash
pytest
```

Es werden sowohl Kernfunktionen als auch Framework-Integrationen (aiohttp, flask, sanic usw.) abgedeckt.

---

## Code-Stil

Verwendete Tools:

- `black` — Formatierung
- `flake8` — Linting
- `isort` — Imports sortieren
- `pre-commit` — Pre-Commit-Hooks

Pre-Commit installieren:

```bash
pre-commit install
```

Manuell ausführen:

```bash
pre-commit run --all-files
```

---

## Git & Pull Requests

1. Forke das Repository
2. Erstelle einen Branch: `feature/dein-feature` oder `fix/dein-fix`
3. Verwende sinnvolle, kleine Commits
4. Öffne einen PR mit Beschreibung:
   - Was wurde geändert oder hinzugefügt?
   - Welche Frameworks sind betroffen?
   - Wie wurde getestet?

---

## Dokumentation

Wenn du APIs oder Verhalten änderst, aktualisiere bitte auch die Dokumentation:

- `docs/en/` (Hauptdokumentation)
- Optional: Übersetzungen (`docs/de/`, `docs/ru/`)

---

## Feedback & Fragen

Du bist unsicher bei einer Idee?  
Eröffne ein GitHub-Issue oder diskutiere mit dem Team — wir helfen gerne weiter!
