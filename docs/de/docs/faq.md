# FAQ (Häufig gestellte Fragen)

Hier findest du Antworten auf häufige Fragen zu FastOpenAPI. Falls deine Frage hier nicht beantwortet wird, kannst du gerne ein Issue auf GitHub eröffnen oder uns direkt kontaktieren.

---

#### **F: Was ist FastOpenAPI und wie unterscheidet es sich von FastAPI?**  
**A:** FastOpenAPI ist kein Webframework, sondern eine Bibliothek, die OpenAPI/Swagger-Dokumentation und Request/Response-Validierung zu bestehenden Webframeworks (wie Flask, AIOHTTP usw.) hinzufügt. FastAPI hingegen ist ein vollständiges Webframework mit integrierter OpenAPI-Unterstützung. FastOpenAPI wurde von FastAPI inspiriert, ist aber dafür gedacht, ähnliche Vorteile in anderen Frameworks bereitzustellen.  
Kurz: Verwende FastAPI, wenn du ein neues Projekt startest. Nutze FastOpenAPI, wenn du bereits ein Projekt in einem anderen Framework hast oder mehrere Frameworks unterstützen möchtest.

#### **F: Welche Webframeworks werden unterstützt?**  
**A:** Unterstützt werden:

- **AIOHTTP** (asynchroner HTTP-Server/Framework)
- **Falcon** (unterstützt ASGI und WSGI)
- **Flask** (klassisches synchrones WSGI-Framework)
- **Quart** (asynchrones Framework mit Flask-ähnlicher API)
- **Sanic** (schnelles asynchrones Framework)
- **Starlette** (leichtgewichtiges ASGI-Framework)
- **Tornado** (Webframework und Netzwerkbibliothek)
- **Django** (Webframework)

FastOpenAPI ist modular und leicht erweiterbar, sodass in Zukunft weitere Adapter folgen können. Du kannst auch einen eigenen `Router` schreiben (siehe Abschnitt "Advanced Usage").

#### **F: Welche Python- und Pydantic-Versionen werden benötigt?**  
**A:** FastOpenAPI erfordert **Python 3.10+** und nutzt **Pydantic v2** zur Validierung und Schema-Generierung. Pydantic v2 erstellt JSON Schema kompatibel mit OpenAPI 3.1.

#### **F: Wie dokumentiert man Authentifizierung (z. B. JWT, API Keys)?**  
**A:** FastOpenAPI implementiert keine Authentifizierungsmechanismen. Diese bleiben Sache des Frameworks. Du kannst aber `securitySchemes` in der OpenAPI-Spezifikation manuell ergänzen (siehe „Advanced Usage“). Wenn du z. B. ein JWT im Header erwartest, kannst du einfach ein `token: str` Argument angeben. Die Validierung erfolgt dann in deiner Middleware oder deinen Decorators.

#### **F: Die Dokumentationsseiten (/docs, /redoc) funktionieren nicht. Was tun?**  
**A:** Stelle sicher, dass du das App-Objekt korrekt übergeben hast (`router = FrameworkRouter(app=app)`). Ohne dies werden keine Routen registriert. Prüfe außerdem, ob dein Server läuft und ob evtl. ein URL-Präfix verwendet wird.

#### **F: Kann man FastOpenAPI mit anderen Schema-Generatoren wie Flask-RESTx kombinieren?**  
**A:** Davon wird abgeraten. Zwei parallele Generatoren können zu Konflikten führen. FastOpenAPI ist als Ersatz konzipiert. Falls du es dennoch einsetzt, deaktiviere andere automatische Dokumentationslösungen.

#### **F: Unterstützt FastOpenAPI Dependency Injection oder Features wie Background Tasks?**  
**A:** Nein. FastOpenAPI kümmert sich nur um Routing, Validierung und Dokumentation. Dependency Injection und Background Tasks müssen vom jeweiligen Framework bereitgestellt werden.

#### **F: Ist FastOpenAPI produktionsreif?**  
**A:** FastOpenAPI befindet sich in aktiver Entwicklung (pre-1.0). Viele Features sind stabil, aber Änderungen sind möglich. Fixiere die Version in `requirements.txt` und teste regelmäßig. Die Schema-Generierung ist sicher, da sie nur lesend arbeitet.

#### **F: Wie kann ich beitragen oder Fehler melden?**  
**A:** Beiträge sind willkommen! Lies den Abschnitt **Contributing**. Du kannst ein Issue oder einen Pull Request auf GitHub erstellen.

#### **F: Gibt es Beispielprojekte, die FastOpenAPI nutzen?**  
**A:** Im Verzeichnis `examples/` des Repos findest du Beispielprojekte für jedes unterstützte Framework. Wenn du FastOpenAPI produktiv einsetzt, freuen wir uns über Links oder Erfahrungsberichte!

#### **F: Welche OpenAPI-Version wird generiert?**  
**A:** FastOpenAPI generiert OpenAPI 3.1.0, da Pydantic v2 JSON Schema in diesem Format ausgibt. Swagger UI und ReDoc unterstützen diese Version.

---

Wenn du weitere Fragen hast, schau auch in die Abschnitte **Usage**, **Advanced** oder ins GitHub-Issue-Tracking. Deine Fragen helfen, das Projekt zu verbessern!
