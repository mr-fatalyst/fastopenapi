from collections.abc import Callable
from typing import Any

from tornado.web import Application, RequestHandler, url

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.tornado.extractors import TornadoRequestDataExtractor
from fastopenapi.routers.tornado.handler import TornadoDynamicHandler
from fastopenapi.routers.tornado.utils import json_encode


class TornadoRouter(BaseAdapter):
    """Tornado adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"(?P<\1>[^/]+)")

    extractor_async_cls = TornadoRequestDataExtractor

    def __init__(self, app: Application | None = None, **kwargs: Any):
        self.routes: list[Any] = []
        self._endpoint_map: dict[str, dict[str, Callable[..., Any]]] = {}
        self._registered_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable[..., Any]) -> None:
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
            for rule in self.routes:  # pragma: no cover
                if rule.matcher.regex.pattern == f"{tornado_path}$":
                    rule.target_kwargs["endpoints"] = self._endpoint_map[tornado_path]
                    break

    def build_framework_response(self, response: WireResponse) -> WireResponse:
        """Tornado applies the triple inside its RequestHandler"""
        return response

    def is_framework_response(self, response: Any) -> bool:
        # Tornado has no response object endpoints could return
        return False

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""
        openapi_url = self.openapi_url
        if openapi_url is None:
            return
        # narrowing does not survive into nested class bodies
        schema_url: str = openapi_url
        router = self

        class OpenAPIHandler(RequestHandler):
            async def get(self) -> None:
                self.set_header("Content-Type", "application/json")
                self.write(json_encode(router.openapi))
                await self.finish()

        class SwaggerUIHandler(RequestHandler):
            async def get(self) -> None:
                html = render_swagger_ui(schema_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        class RedocUIHandler(RequestHandler):
            async def get(self) -> None:
                html = render_redoc_ui(schema_url)
                self.set_header("Content-Type", "text/html")
                self.write(html)
                await self.finish()

        spec_openapi = url(openapi_url, OpenAPIHandler, name="openapi-schema")
        specs = [spec_openapi]

        if self.docs_url:
            spec_swagger = url(self.docs_url, SwaggerUIHandler, name="swagger-ui")
            specs.append(spec_swagger)
        if self.redoc_url:
            spec_redoc = url(self.redoc_url, RedocUIHandler, name="redoc-ui")
            specs.append(spec_redoc)

        self.routes.extend(specs)
        if self.app is not None:
            self.app.add_handlers(r".*", specs)
