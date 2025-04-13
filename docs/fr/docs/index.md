# FastOpenAPI

<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Logo">
</p>

<p align="center">
  <b>FastOpenAPI</b> est une bibliothèque permettant de générer et d'intégrer des schémas OpenAPI à l'aide de Pydantic et de plusieurs frameworks.
</p>

<p align="center">
  Ce projet est inspiré de <a href="https://fastapi.tiangolo.com/">FastAPI</a> et vise à offrir une expérience développeur tout aussi agréable.
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

## À propos du projet

**FastOpenAPI** est une bibliothèque Python permettant de générer et d’intégrer des schémas OpenAPI à partir de modèles Pydantic dans divers frameworks web. Inspirée par FastAPI, elle propose une expérience similaire, mais applicable à des frameworks comme AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette et Tornado.  
Avec FastOpenAPI, vous pouvez ajouter une documentation interactive et une validation automatique à vos projets existants sans changer de framework.

FastOpenAPI est encore en développement actif (pré-version 1.0), mais elle est déjà suffisamment stable pour être utilisée. Toute contribution est la bienvenue !

## Fonctionnalités

- **Génération automatique d’OpenAPI** – définissez vos routes et vos modèles, FastOpenAPI génère automatiquement un schéma complet.
- **Compatible avec Pydantic v2** – validation et sérialisation robustes pour les entrées et les réponses.
- **Multi-framework** – support pour AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette et Tornado.
- **Syntaxe proche de FastAPI** – décorateurs comme `@router.get`, `@router.post`, etc.
- **Documentation interactive intégrée** – Swagger UI (`/docs`) et ReDoc (`/redoc`) inclus.
- **Validation et gestion des erreurs** – erreurs automatiquement retournées en JSON, avec classes standard comme `BadRequestError`, `ResourceNotFoundError`.

Utilisez la navigation à gauche pour parcourir la documentation. Commencez par les sections **Installation** et **Démarrage rapide**, puis passez à **Utilisation**. Chaque framework est traité dans une section dédiée. Les sujets avancés sont regroupés dans **Utilisation avancée** et **Référence API**.  
Vous souhaitez contribuer ? Consultez la section **Contribuer**. Les changements récents sont listés dans le **Changelog**, et les questions fréquentes dans la **FAQ**.

