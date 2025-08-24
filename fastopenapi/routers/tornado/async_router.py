from collections.abc import Callable

from tornado.web import Application, RequestHandler, url

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.tornado.extractors import TornadoRequestDataExtractor
from fastopenapi.routers.tornado.handler import TornadoDynamicHandler
from fastopenapi.routers.tornado.utils import json_encode


class TornadoRouter(BaseAdapter):
    """Tornado adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"(?P<\1>[^/]+)")

    extractor_async_cls = TornadoRequestDataExtractor

    def __init__(self, app: Application = None, **kwargs):
        self.routes = []
        self._endpoint_map: dict[str, dict[str, Callable]] = {}
        self._registered_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Tornado application"""
        super().add_route(path, method, endpoint)

        tornado_path = self._convert_path_for_framework(path)

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

    def build_framework_response(self, response: Response):
        """Build Tornado response - handled directly in handler"""
        return response

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""
        router = self

        class OpenAPIHandler(RequestHandler):
            async def get(self):
                self.set_header("Content-Type", "application/json")
                self.write(json_encode(router.openapi))
                await self.finish()

        class SwaggerUIHandler(RequestHandler):
            async def get(self):
                html = render_swagger_ui(router.openapi_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        class RedocUIHandler(RequestHandler):
            async def get(self):
                html = render_redoc_ui(router.openapi_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        spec_openapi = url(self.openapi_url, OpenAPIHandler, name="openapi-schema")
        spec_swagger = url(self.docs_url, SwaggerUIHandler, name="swagger-ui")
        spec_redoc = url(self.redoc_url, RedocUIHandler, name="redoc-ui")

        self.routes.extend([spec_openapi, spec_swagger, spec_redoc])
        if self.app is not None:
            self.app.add_handlers(r".*", [spec_openapi, spec_swagger, spec_redoc])
