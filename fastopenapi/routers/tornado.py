import inspect
import re
from collections.abc import Callable

from tornado.escape import json_decode, json_encode
from tornado.web import Application, HTTPError, RequestHandler, url

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
        self.endpoint = kwargs.get("endpoint")
        self.router = kwargs.get("router")

    async def prepare(self):
        if self.request.body:
            try:
                self.json_body = json_decode(self.request.body)
            except Exception:
                self.json_body = {}
        else:
            self.json_body = {}

    async def handle_http_exception(self, e):
        self.set_status(e.status_code)
        await self.finish(json_encode({"detail": str(e.log_message)}))

    async def handle_request(self):
        query_params = {
            k: self.get_query_argument(k) for k in self.request.query_arguments
        }

        all_params = {**self.path_kwargs, **query_params}
        body = self.json_body
        try:
            resolved_kwargs = self.router.resolve_endpoint_params(
                self.endpoint, all_params, body
            )
        except Exception as e:
            self.set_status(422)
            await self.finish(json_encode({"detail": str(e)}))
            return
        try:
            if inspect.iscoroutinefunction(self.endpoint):
                result = await self.endpoint(**resolved_kwargs)
            else:
                result = self.endpoint(**resolved_kwargs)
        except Exception as e:
            if isinstance(e, HTTPError):
                await self.handle_http_exception(e)
                return
            self.set_status(422)
            await self.finish(json_encode({"detail": str(e)}))
            return
        meta = getattr(self.endpoint, "__route_meta__", {})
        status_code = meta.get("status_code", 200)
        result = self.router._serialize_response(result)
        self.set_status(status_code)
        self.set_header("Content-Type", "application/json")
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
        super().__init__(app, **kwargs)
        if self.app is not None and (self.add_docs_route or self.add_openapi_route):
            self._register_docs_endpoints()

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)

        tornado_path = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)

        spec = url(
            tornado_path,
            TornadoDynamicHandler,
            name=endpoint.__name__,
            kwargs={"endpoint": endpoint, "router": self},
        )
        self.routes.append(spec)
        if self.app is not None:
            self.app.add_handlers(r".*", [spec])

    def _register_docs_endpoints(self):
        router = self

        class OpenAPIHandler(TornadoDynamicHandler):
            async def get(self):
                self.set_header("Content-Type", "application/json")
                self.write(self.router.openapi)
                await self.finish()

        class SwaggerUIHandler(TornadoDynamicHandler):
            async def get(self):
                html = self.router.render_swagger_ui(self.router.openapi_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        class RedocUIHandler(TornadoDynamicHandler):
            async def get(self):
                html = self.router.render_redoc_ui(self.router.openapi_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        spec_openapi = url(
            self.openapi_url,
            OpenAPIHandler,
            name="openapi-schema",
            kwargs={"router": router},
        )
        spec_swagger = url(
            self.docs_url,
            SwaggerUIHandler,
            name="swagger-ui",
            kwargs={"router": router},
        )
        spec_redoc = url(
            self.redoc_url,
            RedocUIHandler,
            name="redoc-ui",
            kwargs={"router": router},
        )
        self.routes.extend([spec_openapi, spec_swagger, spec_redoc])
        if self.app is not None:
            self.app.add_handlers(r".*", [spec_openapi, spec_swagger, spec_redoc])
