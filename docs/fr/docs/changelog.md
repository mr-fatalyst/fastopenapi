# Journal des modifications (Changelog)

Toutes les modifications importantes de FastOpenAPI sont documentées dans ce fichier.

## [0.5.0] – 2025-04-13

### Ajouté
- **AioHttpRouter** pour l’intégration avec le framework AIOHTTP (prise en charge asynchrone).
- Cache au niveau de la classe pour les schémas de modèles Pydantic (améliore les performances en évitant de régénérer les mêmes schémas).
- Paramètre `response_errors` dans les décorateurs de routes pour documenter les erreurs dans OpenAPI.
- Module `error_handler` pour les réponses d’erreur standardisées (avec classes comme `BadRequestError`, `ResourceNotFoundError`, etc.).
- Prise en charge des types simples (`int`, `float`, `bool`, `str`) comme `response_model`.

## [0.4.0] – 20/03/2025

### Ajouté
- Prise en charge de **ReDoc UI** (disponible sur `/redoc`).
- **TornadoRouter** pour le framework Tornado.

### Modifié
- Refactorisation des tests pour améliorer la couverture et la fiabilité.

### Corrigé
- Erreurs internes : passage du code 422 à 500 (conformité HTTP).

### Supprimé
- Méthodes `add_docs_route` et `add_openapi_route` retirées de `BaseRouter` (les routes sont maintenant ajoutées automatiquement).

## [0.3.1] – 15/03/2025

### Corrigé
- Erreur d'importation lorsque les frameworks ne sont pas installés (`ModuleNotFoundError` géré).

## [0.3.0] – 15/03/2025

### Ajouté
- **QuartRouter** pour le framework Quart (async).
- Première version de la documentation (introduction et exemples).

### Modifié
- Simplification de l'import : `from fastopenapi.routers import YourRouter`.

### Corrigé
- Prise en charge correcte des modèles Pydantic dans les requêtes GET.

## [0.2.1] – 12/03/2025

### Corrigé
- Problème de sérialisation : `_serialize_response` convertit maintenant les modèles en `dict` avant de les encoder.
- Correction de cas d’erreur dans `DataLoader` avec données vides.
- Tests supplémentaires pour couvrir ces cas.
- Ajout de ce fichier `CHANGELOG.md`.

## [0.2.0] – 11/03/2025

### Ajouté
- Fonction `resolve_endpoint_params` dans `BaseRouter` (extraction de paramètres : path, query, body).
- Prise en charge du `prefix` dans `include_router` pour grouper les routes.
- Prise en charge du paramètre `status_code` dans les décorateurs.

### Modifié
- Refactorisation des routeurs pour plus de cohérence et de réutilisabilité.

### Supprimé
- Suppression de `register_routes` dans l’implémentation Starlette (obsolète après refactorisation).

## [0.1.0] – 01/03/2025

### Ajouté
- Première publication de FastOpenAPI.
- Fonctionnalités de base :
  - Classe `BaseRouter`
  - Prise en charge de Falcon, Flask, Sanic, Starlette
  - Génération d’OpenAPI via Pydantic v2
  - Validation des paramètres et corps
- Ajout du README et d’exemples simples.
- Tests initiaux de génération de schéma et d’enregistrement des routes.
