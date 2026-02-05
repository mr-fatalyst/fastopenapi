# Advanced Usage

In this section, we'll explore advanced topics such as FastOpenAPI's architecture, extending it to new frameworks, and customizing the generated documentation or behavior. This is geared more towards developers who want to understand or modify FastOpenAPI's internals or integrate it in non-standard ways.

## Architecture Overview

FastOpenAPI's design is inspired by FastAPI, but it is framework-agnostic. The core components include:

- **BaseRouter**: A core class that contains logic for registering routes, generating the OpenAPI schema, and handling requests/responses. It is not tied to any one framework.
- **Framework-specific Routers**: Subclasses of BaseRouter like `FlaskRouter`, `StarletteRouter`, etc. These implement the small differences required to hook into each framework (for example, how to actually register a route or how to attach the docs routes).
- **Pydantic Models**: FastOpenAPI relies on Pydantic for data modeling. Pydantic is used to define request bodies and responses, and to produce JSON Schema representations for the OpenAPI spec.
- **OpenAPI Schema Generation**: FastOpenAPI uses the metadata from your routes (paths, methods, parameters, models, etc.) to build an OpenAPI schema (version 3.1.0, as Pydantic v2 outputs JSON Schema compatible with OpenAPI 3.1). The schema is produced in JSON and served via the `/openapi.json` endpoint.
- **Documentation UIs**: FastOpenAPI includes static assets or references for Swagger UI and ReDoc. When you access `/docs` or `/redoc`, the router serves an HTML page that pulls in the respective UI (Swagger or ReDoc) and points it to the generated `/openapi.json`.

## Flow of a typical request

1. A request comes into your web framework (say, Flask) for one of the documented routes.
2. The request is routed to a handler function that was registered via FastOpenAPI (using the `@router.get/post/...` decorator).
3. Before calling your function, FastOpenAPI (BaseRouter) will parse and validate input:
   - Path params are extracted from the URL (the framework usually does this part).
   - Query params, headers, and body are parsed. Query and path params are validated against the function signature (types or Pydantic models). Body is parsed into Pydantic models if specified.
4. Your route function executes with the validated parameters. (If any validation failed, FastOpenAPI would have already returned an error response, so your function won't run in that case.)
5. You return either data or raise an exception:
   - If data is returned, FastOpenAPI will post-process it. If a `response_model` is specified, it validates and serializes the data. If not, it tries to serialize the return value directly.
   - If an exception (like those from `fastopenapi.error_handler`) is raised, FastOpenAPI catches it and generates the appropriate error response.
6. The framework then sends the final response to the client (which is typically JSON for both success and error cases).

## Extending to New Frameworks

One of FastOpenAPI's goals is to be extensible. If you have a framework that’s not supported out-of-the-box, you can potentially create a new router for it.

To create a new integration:

<ul>
  <li>Subclass <code>fastopenapi.routers.BaseRouter</code>.</li>
  <li>Implement necessary abstract methods. For example, BaseRouter requires something like:
    <ul>
      <li>A method to <strong>add a route</strong> to the underlying framework.</li>
      <li>Perhaps a method to start the application (though many frameworks don't need that encapsulated in the router).</li>
      <li>Ensure that the documentation routes (<code>/docs</code>, <code>/redoc</code>, <code>/openapi.json</code>) are added to the app. (In existing routers, this is often done in the BaseRouter constructor or via a helper method that each router calls.)</li>
    </ul>
  </li>
  <li>Look at how existing routers are implemented. For instance, <code>FlaskRouter.add_route</code> will call <code>Flask.app.add_url_rule</code>, whereas <code>StarletteRouter.add_route</code> will add it to <code>Starlette.routes</code>.</li>
  <li>The BaseRouter provides utility functions for generating the OpenAPI spec (<code>BaseRouter.get_openapi_schema()</code> or similar) which framework routers can use.</li>
</ul>

For example, if integrating with **Fastify (hypothetical)**, you would write a `FastifyRouter(BaseRouter)` and implement how to register routes in Fastify (though Fastify is Node.js, so this is just a thought exercise).

Another scenario for extension is if you want to customize how something works in an existing router:

- You could subclass an existing router class and override methods. For instance, if you wanted a special version of `FlaskRouter` that registers routes under a URL prefix or modifies the docs path, you could subclass and change that behavior.
- You might also modify error handling or schema generation by overriding parts of BaseRouter, but that requires understanding of the internals.
