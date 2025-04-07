import inspect
import re
from collections.abc import Callable

from tornado.escape import json_decode, json_encode
from tornado.web import Application, RequestHandler, url

from fastopenapi.base_router import BaseRouter


class TornadoDynamicHandler(RequestHandler):
    """
    A dynamic request handler for Tornado, which resolves endpoint parameters and
    serializes the response using the router's logic.

    The handler is initialized with:
      - endpoint: The view function (endpoint) to be called.
      - router: The instance of TornadoRouter that provides methods like
       resolve_endpoint_params and _serialize_response.
    """

    def initialize(self, **kwargs):
        self.endpoints = kwargs.get("endpoints", {})
        self.router = kwargs.get("router")

    async def prepare(self):
        if self.request.body:
            try:
                self.json_body = json_decode(self.request.body)
            except Exception:
                self.json_body = {}
        else:
            self.json_body = {}
        self.endpoint = self.endpoints.get(self.request.method.upper())

    async def handle_http_exception(self, e):
        self.set_status(e.status_code)
        await self.finish(json_encode({"detail": str(e.log_message)}))

    async def handle_request(self):
        if not hasattr(self, "endpoint") or not self.endpoint:
            self.send_error(405)
            return

        query_params = {
            k: self.get_query_argument(k) for k in self.request.query_arguments
        }

        all_params = {**self.path_kwargs, **query_params}
        body = getattr(self, "json_body", {})
        try:
            resolved_kwargs = self.router.resolve_endpoint_params(
                self.endpoint, all_params, body
            )
        except Exception as e:
            error_response = self.router.handle_exception(e)
            self.set_status(getattr(e, "status_code", 422))
            self.set_header("Content-Type", "application/json")
            await self.finish(json_encode(error_response))
            return
        try:
            if inspect.iscoroutinefunction(self.endpoint):
                result = await self.endpoint(**resolved_kwargs)
            else:
                result = self.endpoint(**resolved_kwargs)
        except Exception as e:
            error_response = self.router.handle_exception(e)
            self.set_status(getattr(e, "status_code", 500))
            self.set_header("Content-Type", "application/json")
            await self.finish(json_encode(error_response))
            return
        meta = getattr(self.endpoint, "__route_meta__", {})
        status_code = meta.get("status_code", 200)
        result = self.router._serialize_response(result)
        self.set_status(status_code)
        self.set_header("Content-Type", "application/json")
        if status_code == 204:
            await self.finish()
        else:
            await self.finish(json_encode(result))

    async def get(self, *args, **kwargs):
        await self.handle_request()

    async def post(self, *args, **kwargs):
        await self.handle_request()

    async def put(self, *args, **kwargs):
        await self.handle_request()

    async def patch(self, *args, **kwargs):
        await self.handle_request()

    async def delete(self, *args, **kwargs):
        await self.handle_request()


class TornadoRouter(BaseRouter):
    def __init__(self, app: Application = None, **kwargs):
        self.routes = []
        self._endpoint_map: dict[str, dict[str, Callable]] = {}
        self._registered_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)

        tornado_path = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)

        if tornado_path not in self._endpoint_map:
            self._endpoint_map[tornado_path] = {}
        self._endpoint_map[tornado_path][method.upper()] = endpoint

        if tornado_path not in self._registered_paths:
            self._registered_paths.add(tornado_path)
            spec = url(
                tornado_path,
                TornadoDynamicHandler,
                name=f"route_{len(self._registered_paths)}",
                kwargs={"endpoints": self._endpoint_map[tornado_path], "router": self},
            )
            self.routes.append(spec)
            if self.app is not None:
                self.app.add_handlers(r".*", [spec])
        else:
            for rule in self.routes:
                if rule.matcher.regex.pattern == f"{tornado_path}$":
                    rule.target_kwargs["endpoints"] = self._endpoint_map[tornado_path]
                    break

    def _register_docs_endpoints(self):
        router = self

        class OpenAPIHandler(RequestHandler):
            async def get(self):
                self.set_header("Content-Type", "application/json")
                self.write(json_encode(router.openapi))
                await self.finish()

        class SwaggerUIHandler(RequestHandler):
            async def get(self):
                html = router.render_swagger_ui(router.openapi_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        class RedocUIHandler(RequestHandler):
            async def get(self):
                html = router.render_redoc_ui(router.openapi_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        spec_openapi = url(
            self.openapi_url, OpenAPIHandler, name="openapi-schema", kwargs={}
        )
        spec_swagger = url(
            self.docs_url, SwaggerUIHandler, name="swagger-ui", kwargs={}
        )
        spec_redoc = url(self.redoc_url, RedocUIHandler, name="redoc-ui", kwargs={})
        self.routes.extend([spec_openapi, spec_swagger, spec_redoc])
        if self.app is not None:
            self.app.add_handlers(r".*", [spec_openapi, spec_swagger, spec_redoc])
