# Utilisation avancée

Dans cette section, nous abordons des sujets avancés comme l'architecture de FastOpenAPI, son extension à de nouveaux frameworks et la personnalisation du comportement ou de la documentation générée. Elle s’adresse aux développeurs qui souhaitent comprendre les rouages internes ou intégrer FastOpenAPI de manière plus poussée.

## Vue d’ensemble de l’architecture

La conception de FastOpenAPI est inspirée de FastAPI, mais indépendante de tout framework. Ses composants principaux sont :

- **BaseRouter** : Classe de base centrale gérant le routage, la génération de schémas OpenAPI et la validation des requêtes/réponses.
- **Routeurs spécifiques à chaque framework** : Sous-classes de `BaseRouter` (par exemple, `FlaskRouter`, `StarletteRouter`, etc.) qui assurent l’intégration avec les frameworks ciblés.
- **Modèles Pydantic** : Pour définir, valider et documenter les données d’entrée/sortie.
- **Génération OpenAPI** : FastOpenAPI construit un schéma OpenAPI 3.1 basé sur les routes et les métadonnées définies.
- **Documentation automatique** : Rendu interactif via Swagger UI (`/docs`) et ReDoc (`/redoc`), et export JSON (`/openapi.json`).

## Cycle de traitement d’une requête

1. Une requête HTTP est reçue par le framework.
2. FastOpenAPI intercepte la route via un décorateur `@router.get`, `@router.post`, etc.
3. Extraction des paramètres (path, query, body), validation via Pydantic.
4. En cas d’échec de validation, une réponse structurée avec code 400 ou 422 est renvoyée.
5. Si tout est valide, la fonction est appelée avec des arguments typés.
6. La réponse est également validée via `response_model`, puis encodée en JSON.
7. Les exceptions types `BadRequestError`, `ResourceNotFoundError` sont converties automatiquement.

## Étendre à d'autres frameworks

FastOpenAPI est conçu pour être facilement extensible.

### Étapes :

- Créez une nouvelle classe héritant de `BaseRouter`
- Implémentez :
  - `add_route()`
  - (Optionnel) `include_router()`
  - L’ajout de `/docs`, `/redoc`, `/openapi.json` si nécessaire

### Exemple :

```python
from fastopenapi.base_router import BaseRouter

class MyCustomRouter(BaseRouter):
    def add_route(self, path, method, handler):
        # Logique propre au framework
        pass
```

Inspirez-vous de `starlette.py`, `flask.py`, etc. pour voir des implémentations concrètes.

---

FastOpenAPI vise à rester minimaliste, extensible, et compatible avec les outils modernes de typage et de documentation Python.
