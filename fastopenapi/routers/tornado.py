import inspect
import re
from collections.abc import Callable

from pydantic_core import from_json, to_json
from tornado.web import Application, RequestHandler, url

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


def json_encode(data):
    """Encode data to JSON with safe escaping"""
    return to_json(data).decode("utf-8").replace("</", "<\\/")


class TornadoDynamicHandler(RequestHandler):
    """Dynamic request handler for Tornado"""

    def initialize(self, **kwargs):
        self.endpoints = kwargs.get("endpoints", {})
        self.router = kwargs.get("router")

    async def prepare(self):
        """Prepare request data"""
        if self.request.body:
            try:
                self.json_body = from_json(self.request.body)
            except Exception:
                self.json_body = {}
        else:
            self.json_body = {}
        self.endpoint = self.endpoints.get(self.request.method.upper())

    async def handle_request(self):
        """Common request handling"""
        if not hasattr(self, "endpoint") or not self.endpoint:
            self.send_error(405)
            return

        # Create synthetic request
        synthetic_request = type(
            "Request",
            (),
            {
                "path_kwargs": self.path_kwargs,
                "request": self.request,
                "json_body": getattr(self, "json_body", {}),
            },
        )()

        # Check if endpoint is async and use appropriate handler
        if inspect.iscoroutinefunction(self.endpoint):
            result_response = await self.router.handle_request_async(
                self.endpoint, synthetic_request
            )
        else:
            result_response = self.router.handle_request_sync(
                self.endpoint, synthetic_request
            )

        # Handle Response object
        if isinstance(result_response, Response):
            self.set_status(result_response.status_code)
            self.set_header("Content-Type", "application/json")

            # Set custom headers
            for key, value in result_response.headers.items():
                self.set_header(key, value)

            if result_response.status_code == 204:
                await self.finish()
            else:
                await self.finish(json_encode(result_response.content))

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

    async def head(self, *args, **kwargs):
        await self.handle_request()

    async def options(self, *args, **kwargs):
        await self.handle_request()


class TornadoRouter(BaseAdapter):
    """Tornado adapter for FastOpenAPI"""

    def __init__(self, app: Application = None, **kwargs):
        self.routes = []
        self._endpoint_map: dict[str, dict[str, Callable]] = {}
        self._registered_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Tornado application"""
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
            # Update existing route
            for rule in self.routes:
                if rule.matcher.regex.pattern == f"{tornado_path}$":
                    rule.target_kwargs["endpoints"] = self._endpoint_map[tornado_path]
                    break

    def extract_request_data(self, synthetic_request) -> RequestData:
        """Extract data from Tornado request"""
        request = synthetic_request.request
        path_kwargs = synthetic_request.path_kwargs

        # Query parameters
        query_params = {}
        for key in request.query_arguments:
            values = [v.decode("utf-8") for v in request.query_arguments[key]]
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = {}
        for name, value in request.cookies.items():
            cookies[name] = value.value

        # Body
        body = getattr(synthetic_request, "json_body", {})

        # Form data and files
        form_data = {}
        files = {}
        if request.body_arguments:
            for key, values in request.body_arguments.items():
                decoded_values = [v.decode("utf-8") for v in values]
                form_data[key] = (
                    decoded_values[0] if len(decoded_values) == 1 else decoded_values
                )

        if request.files:
            for name, file_list in request.files.items():
                if file_list:
                    file = file_list[0]
                    files[name] = UploadFile(
                        filename=file["filename"],
                        content_type=file.get("content_type", ""),
                        file=file["body"],
                    )

        return RequestData(
            path_params=path_kwargs or {},
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            form_data=form_data,
            files=files,
        )

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
