# Installation

FastOpenAPI est disponible sur PyPI et prend en charge **Python 3.10 ou supérieur**. Vous pouvez installer uniquement la bibliothèque principale ou inclure des dépendances optionnelles pour certains frameworks web.

## Prérequis

- **Python 3.10 ou plus récent** – requis en raison de l'utilisation des fonctionnalités modernes de typage et de Pydantic v2.
- (Optionnel) Un framework web existant (comme Flask, Starlette, etc.) si vous prévoyez une intégration. Si vous ne l'avez pas encore installé, vous pouvez utiliser les extras de `pip` pour l’installer automatiquement avec FastOpenAPI.

## Utilisation de pip

#### Installer uniquement FastOpenAPI  
*Installation standard :*
```bash
pip install fastopenapi
```

#### Installer FastOpenAPI avec un framework spécifique  
*Utile si vous commencez un nouveau projet sans framework installé :*
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
