# FAQ (Foire Aux Questions)

Voici les réponses aux questions fréquentes concernant FastOpenAPI. Si vous avez d'autres questions, n'hésitez pas à ouvrir une issue sur GitHub ou à nous contacter.

---

#### **Q : Qu'est-ce que FastOpenAPI et en quoi est-ce différent de FastAPI ?**  
**R :** FastOpenAPI n'est pas un framework web, mais une bibliothèque qui ajoute la documentation OpenAPI/Swagger et la validation des requêtes/réponses aux frameworks existants comme Flask, AIOHTTP, etc.  
FastAPI, quant à lui, est un framework complet qui intègre tout cela nativement.  
En résumé : utilisez FastAPI pour un nouveau projet. Utilisez FastOpenAPI si vous avez déjà un projet avec un autre framework.

#### **Q : Quels frameworks sont pris en charge ?**  
**R :** Actuellement, FastOpenAPI prend en charge :
- **AIOHTTP**
- **Falcon**
- **Flask**
- **Quart**
- **Sanic**
- **Starlette**
- **Tornado**

FastOpenAPI est modulaire et peut être étendu facilement. Vous pouvez également créer votre propre `Router` (voir la section "Utilisation avancée").

#### **Q : Quelles versions de Python et Pydantic sont requises ?**  
**R :** Python **3.10 ou supérieur** et Pydantic **v2**. FastOpenAPI utilise le typage moderne de Python et la génération de schéma JSON de Pydantic v2.

#### **Q : Comment documenter l'authentification (JWT, clés API, etc.) ?**  
**R :** FastOpenAPI ne gère pas directement l'authentification. Vous pouvez ajouter manuellement des `securitySchemes` dans le schéma OpenAPI (voir "Utilisation avancée"). Par exemple, vous pouvez définir un paramètre `token: str` et gérer la validation via un middleware ou un décorateur externe.

#### **Q : Les pages /docs ou /redoc ne s'affichent pas ?**  
**R :** Vérifiez que vous avez bien passé l’instance `app` lors de l’initialisation du routeur :  
`router = FrameworkRouter(app=app)`  
Sinon, les routes de documentation ne seront pas ajoutées. Assurez-vous aussi que le serveur démarre correctement et qu’il n’y a pas de préfixe d’URL bloquant l’accès.

#### **Q : Peut-on utiliser FastOpenAPI avec d'autres bibliothèques comme Flask-RESTx ?**  
**R :** Ce n'est pas recommandé. L'utilisation simultanée de plusieurs outils générant des schémas OpenAPI peut causer des conflits. FastOpenAPI est prévu pour fonctionner seul.

#### **Q : Y a-t-il une gestion de l'injection de dépendances ou des tâches en arrière-plan ?**  
**R :** Pas directement. FastOpenAPI se concentre sur la documentation et la validation. Ces fonctionnalités doivent être prises en charge par le framework utilisé.

#### **Q : Est-ce prêt pour un usage en production ?**  
**R :** FastOpenAPI est encore en développement actif (version pré-1.0), mais suffisamment stable pour de nombreux cas. Il est conseillé de fixer la version dans `requirements.txt` et de tester avant tout déploiement.

#### **Q : Comment contribuer ou signaler un bug ?**  
**R :** Avec plaisir ! Consultez la section **Contribuer**. Vous pouvez ouvrir une issue ou un pull request sur GitHub.

#### **Q : Existe-t-il des projets d'exemple utilisant FastOpenAPI ?**  
**R :** Oui, vous trouverez des exemples pour chaque framework dans le dossier `examples/` du dépôt. Si vous utilisez FastOpenAPI en production, faites-le nous savoir !

#### **Q : Quelle version d'OpenAPI est générée ?**  
**R :** FastOpenAPI génère un schéma OpenAPI 3.1.0, car Pydantic v2 produit un schéma JSON compatible avec cette version.

---

Vous avez d'autres questions ? Consultez les sections **Utilisation**, **Avancé** ou ouvrez une issue sur GitHub. Vos retours sont précieux pour améliorer le projet.
