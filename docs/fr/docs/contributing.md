# Bienvenue !

Merci de vouloir contribuer à **FastOpenAPI** 🎉  
Ce guide vous explique comment démarrer, proposer des contributions, écrire des commits, ouvrir des pull requests et exécuter les tests.

---

## Configuration et exécution

Installez les dépendances avec :

```bash
git clone https://github.com/yourusername/fastopenapi.git
cd fastopenapi
poetry install
```

Si vous n’utilisez pas `poetry`, vous pouvez installer manuellement :

```bash
pip install -e .[dev]
```

---

## Structure du projet

- `fastopenapi/` — bibliothèque principale
- `examples/` — exemples pour chaque framework
- `tests/` — tests unitaires
- `benchmarks/` — tests de performance
- `docs/` — documentation multi-langue

---

## Exécution des tests

Lancez tous les tests avec :

```bash
pytest
```

Les tests couvrent la logique principale ainsi que l’intégration avec les frameworks supportés.

---

## Style de code

Outils utilisés :

- `black` — formatage automatique
- `flake8` — linting
- `isort` — tri des imports
- `pre-commit` — hooks avant commit

Installer les hooks :

```bash
pre-commit install
```

Lancer manuellement :

```bash
pre-commit run --all-files
```

---

## Git & Pull Requests

1. Forkez le dépôt
2. Créez une branche : `feature/ma-fonction` ou `fix/mon-correctif`
3. Faites des commits clairs et isolés
4. Ouvrez une pull request avec une description :
   - Ce qui a été changé ou ajouté
   - Quels frameworks sont affectés
   - Comment cela a été testé

---

## Documentation

Si vous modifiez l’API publique ou le comportement, pensez à mettre à jour la documentation :

- Dossier `docs/en/` (principal)
- Optionnellement : traductions dans `docs/fr/`, `docs/de/`, etc.

---

## Feedback & questions

Un doute ?  
Ouvrez une issue ou discutez dans le dépôt — nous serons ravis de vous aider !

