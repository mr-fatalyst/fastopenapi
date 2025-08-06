import inspect
from collections.abc import Callable
from http import HTTPStatus

import falcon.asgi
from pydantic_core import from_json

from fastopenapi.core.types import RequestData, Response
from fastopenapi.errors.handler import format_exception_response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter

# Mapping HTTP status to Falcon constants
HTTP_STATUS_TO_FALCON = {
    HTTPStatus.OK: falcon.HTTP_200,
    HTTPStatus.CREATED: falcon.HTTP_201,
    HTTPStatus.NO_CONTENT: falcon.HTTP_204,
    HTTPStatus.BAD_REQUEST: falcon.HTTP_400,
    HTTPStatus.UNAUTHORIZED: falcon.HTTP_401,
    HTTPStatus.FORBIDDEN: falcon.HTTP_403,
    HTTPStatus.NOT_FOUND: falcon.HTTP_404,
    HTTPStatus.UNPROCESSABLE_ENTITY: falcon.HTTP_422,
    HTTPStatus.INTERNAL_SERVER_ERROR: falcon.HTTP_500,
}

# Method mapping
METHODS_MAPPER = {
    "GET": "on_get",
    "POST": "on_post",
    "PUT": "on_put",
    "PATCH": "on_patch",
    "DELETE": "on_delete",
    "HEAD": "on_head",
    "OPTIONS": "on_options",
}


class FalconRouter(BaseAdapter):
    """Falcon adapter for FastOpenAPI"""

    def __init__(self, app: falcon.asgi.App = None, **kwargs):
        self._resources = {}
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Falcon application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            resource = self._create_or_update_resource(path, method.upper(), endpoint)
            self.app.add_route(path, resource)

    def _create_or_update_resource(self, path: str, method: str, endpoint):
        """Create or update Falcon resource"""
        resource = self._resources.get(path)
        if not resource:
            resource = type("DynamicResource", (), {})()
            self._resources[path] = resource

        method_name = METHODS_MAPPER.get(method, f"on_{method.lower()}")

        async def handle(req, resp, **path_params):
            await self.handle_falcon_request(endpoint, req, resp, **path_params)

        setattr(resource, method_name, handle)
        return resource

    async def handle_falcon_request(self, endpoint, req, resp, **path_params):
        """Handle Falcon request"""
        try:
            # Create synthetic request
            synthetic_request = type(
                "Request",
                (),
                {
                    "path_params": path_params,
                    "params": req.params,
                    "bounded_stream": req.bounded_stream,
                    "headers": req.headers,
                    "cookies": req.cookies,
                },
            )()

            request_data = await self.extract_request_data_async(synthetic_request)
            kwargs = self.resolver.resolve(endpoint, request_data)

            # Call endpoint
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)

            response_obj = self.response_builder.build(result, endpoint.__route_meta__)

            # Set response
            resp.status = self._get_falcon_status(response_obj.status_code)
            resp.media = response_obj.content

            # Set headers
            for key, value in response_obj.headers.items():
                resp.set_header(key, value)

        except Exception as e:
            error_response = format_exception_response(e)
            resp.status = self._get_falcon_status(getattr(e, "status_code", 500))
            resp.media = error_response

    async def extract_request_data_async(self, request) -> RequestData:
        """Extract data from Falcon request (async)"""
        # Query parameters
        query_params = {}
        for key in request.params.keys():
            values = (
                request.params.getall(key)
                if hasattr(request.params, "getall")
                else [request.params.get(key)]
            )
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        # Body
        body = {}
        try:
            body_bytes = await request.bounded_stream.read()
            if body_bytes:
                body = from_json(body_bytes.decode("utf-8"))
        except Exception:
            pass

        # Form data and files - Falcon doesn't have built-in multipart support
        # You'd need to use a library like python-multipart for this
        form_data = {}
        files = {}

        return RequestData(
            path_params=getattr(request, "path_params", {}),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            form_data=form_data,
            files=files,
        )

    def extract_request_data(self, request) -> RequestData:
        """Not used in async adapter"""
        raise NotImplementedError("Use extract_request_data_async")

    def build_framework_response(self, response: Response):
        """Not needed for Falcon (handled in handle_falcon_request)"""

    def _get_falcon_status(self, status_code: int) -> str:
        """Get Falcon status constant"""
        http_status = HTTPStatus(status_code)
        return HTTP_STATUS_TO_FALCON.get(http_status, falcon.HTTP_500)

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""
        outer = self

        class OpenAPISchemaResource:
            async def on_get(self, req, resp):
                resp.media = outer.openapi

        class SwaggerUIResource:
            async def on_get(self, req, resp):
                html = render_swagger_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        class RedocUIResource:
            async def on_get(self, req, resp):
                html = render_redoc_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        self.app.add_route(self.openapi_url, OpenAPISchemaResource())
        self.app.add_route(self.docs_url, SwaggerUIResource())
        self.app.add_route(self.redoc_url, RedocUIResource())
