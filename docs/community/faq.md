# FAQ (Frequently Asked Questions)

Below are answers to common questions about FastOpenAPI. If you have a question that isn’t covered here, feel free to reach out or open an issue on GitHub.

---

#### **Q: What is FastOpenAPI and how is it different from FastAPI?**  
**A:** FastOpenAPI is not a web framework by itself, but a library to add OpenAPI/Swagger documentation and request/response validation to existing web frameworks (Flask, AIOHTTP, etc.). FastAPI is a full web framework that integrates OpenAPI generation natively. FastOpenAPI was inspired by FastAPI’s developer experience but aims to provide similar benefits for frameworks that don't have automatic docs. In short: use FastAPI if you’re starting fresh and want an integrated solution; use FastOpenAPI if you already have an app in another framework or need to support multiple frameworks with one tool.

#### **Q: Which web frameworks are supported by FastOpenAPI?**  
**A:** Currently supported frameworks are:

- **AIOHTTP** (asyncio-based HTTP server/framework)
- **Falcon** (both ASGI and WSGI usage)
- **Flask** (synchronous WSGI framework)
- **Quart** (Flask-like async framework)
- **Sanic** (async Python web framework)
- **Starlette** (lightweight ASGI framework)
- **Tornado** (Python web framework and networking library)
- **Django** (Python web framework)
These cover a wide range of popular Python frameworks. The architecture allows adding more, so future versions might include others. If you have a need for an unsupported framework, you could attempt to create a custom router (see Advanced Usage) or suggest it to the maintainers.

#### **Q: What versions of Python and Pydantic are required?**  
**A:** FastOpenAPI requires **Python 3.10 or above**. It uses **Pydantic v2** for data modeling and validation. Pydantic v2 outputs OpenAPI 3.1-compatible schemas. Ensure that your environment meets these requirements. (Pydantic v2 comes installed with FastOpenAPI by default.)

#### **Q: How do I handle authentication or API keys in documentation?**
**A:** FastOpenAPI provides built-in security support inspired by FastAPI (but not an exact copy of its API). You can use `Security(dependency_func)` for dependency-based authentication, `SecurityScopes` for OAuth2 scopes, and pre-defined security schemes (`SecuritySchemeType.BEARER_JWT`, `SecuritySchemeType.API_KEY`, etc.) that are automatically reflected in the OpenAPI schema. See the **Security** section of the guide for examples.

#### **Q: The docs UI (Swagger/ReDoc) isn't showing up or `/docs` returns 404. What did I do wrong?**  
**A:** Make sure you initialized the router with your app (`router = FrameworkRouter(app=app)`). If you forget to pass the `app`, the routes won't be registered. Also ensure your app is running and listening on the correct host/port. If running behind a proxy or under a sub-path, you might need to adjust where you look for `/docs`. By default, FastOpenAPI uses root paths for docs. If your app is mounted under a prefix, the docs might be at `/<prefix>/docs`. 

#### **Q: My framework already has some docs or schema generator. Can I use FastOpenAPI alongside it?**  
**A:** If your framework has its own docs generator (like Flask-RESTx or others), it's not recommended to use two documentation generators simultaneously—they might conflict or produce duplicate routes. FastOpenAPI is meant to be a standalone solution. If you choose FastOpenAPI, disable or avoid other documentation plugins for that app to prevent collisions on routes like `/docs`. If you have a specific use case to merge them, you'd likely need to do something custom.

#### **Q: Does FastOpenAPI support dependency injection or other FastAPI features (background tasks, middleware injection, etc.)?**
**A:** Yes, FastOpenAPI provides a FastAPI-like dependency injection system (inspired by FastAPI, but not a complete replica). You can use `Depends(func)` for regular dependencies, `Security(func, scopes=[...])` for security dependencies, and `SecurityScopes` for scope injection. The DI system supports recursive resolution, request-scoped caching, circular dependency detection, async dependencies, and generator (yield) dependencies with cleanup. Background tasks and middleware injection are not provided — use your framework's built-in mechanisms for those.

#### **Q: How stable is FastOpenAPI for production use?**  
**A:** FastOpenAPI is currently in **beta (1.0.0b1)**. Core features (routing, validation, DI, security, OpenAPI generation) are in place and actively tested across 8 frameworks. You should pin a version in production to avoid unexpected breaking changes on upgrade. It's recommended to write tests around critical API functionality in your project to catch any integration issues. The core of using Pydantic for validation is robust, and generating docs is read-only for your app, so the risk is manageable if you test your API.

#### **Q: How can I contribute or report an issue?**  
**A:** We welcome contributions! Check out the **Contributing** section of this documentation for guidelines. You can open issues on the GitHub repository for bugs, feature requests, or questions. If you have code to contribute, please fork the repo and open a Pull Request. Improving documentation, adding examples, and writing tests are also great ways to help.

#### **Q: Are there any examples of real projects using FastOpenAPI?**  
**A:** The FastOpenAPI repository includes an `examples/` directory covering each framework (AIOHTTP, Flask, etc.). Those can serve as a starting point. Since the project is new, real-world usage might not be widely publicized yet, but you can search the repository issues or discussions for any references to usage. Over time, as the user base grows, we expect more community examples. If you successfully use FastOpenAPI in your project, consider sharing your experience or a link for others to learn from!

#### **Q: What OpenAPI version does FastOpenAPI generate?**  
**A:** FastOpenAPI generates an OpenAPI 3.1.0 schema (because Pydantic v2’s JSON Schema output is aligned with OpenAPI 3.1). This means you can use newer features of OpenAPI (like `oneOf`, `anyOf` better support, etc.). Swagger UI and ReDoc both support OpenAPI 3.1 as of their recent versions, so the docs should display correctly. If you encounter an issue with the documentation display, ensure you have a recent version of Swagger UI/ReDoc (the ones bundled with FastOpenAPI should be up to date).

---

If your question wasn’t answered here, please consult the other sections of this documentation. The **Usage** and **Advanced** sections cover many details. You can also look at the repository’s README and issues for more insights. FastOpenAPI is community-driven, and questions or issues you bring up could help improve the project for everyone.