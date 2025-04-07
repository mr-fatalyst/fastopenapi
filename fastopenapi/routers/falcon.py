import inspect
import json
from collections.abc import Callable
from http import HTTPStatus

import falcon.asgi

from fastopenapi.base_router import BaseRouter

METHODS_MAPPER = {
    "GET": "on_get",
    "POST": "on_post",
    "PUT": "on_put",
    "PATCH": "on_patch",
    "DELETE": "on_delete",
}

HTTP_STATUS_TO_FALCON = {
    HTTPStatus.OK: falcon.HTTP_200,
    HTTPStatus.CREATED: falcon.HTTP_201,
    HTTPStatus.ACCEPTED: falcon.HTTP_202,
    HTTPStatus.NO_CONTENT: falcon.HTTP_204,
    HTTPStatus.MOVED_PERMANENTLY: falcon.HTTP_301,
    HTTPStatus.FOUND: falcon.HTTP_302,
    HTTPStatus.SEE_OTHER: falcon.HTTP_303,
    HTTPStatus.NOT_MODIFIED: falcon.HTTP_304,
    HTTPStatus.BAD_REQUEST: falcon.HTTP_400,
    HTTPStatus.UNAUTHORIZED: falcon.HTTP_401,
    HTTPStatus.FORBIDDEN: falcon.HTTP_403,
    HTTPStatus.NOT_FOUND: falcon.HTTP_404,
    HTTPStatus.METHOD_NOT_ALLOWED: falcon.HTTP_405,
    HTTPStatus.CONFLICT: falcon.HTTP_409,
    HTTPStatus.GONE: falcon.HTTP_410,
    HTTPStatus.UNPROCESSABLE_ENTITY: falcon.HTTP_422,
    HTTPStatus.INTERNAL_SERVER_ERROR: falcon.HTTP_500,
    HTTPStatus.NOT_IMPLEMENTED: falcon.HTTP_501,
    HTTPStatus.BAD_GATEWAY: falcon.HTTP_502,
    HTTPStatus.SERVICE_UNAVAILABLE: falcon.HTTP_503,
    HTTPStatus.GATEWAY_TIMEOUT: falcon.HTTP_504,
}


def get_falcon_status(http_status):
    return HTTP_STATUS_TO_FALCON.get(http_status, falcon.HTTP_500)


def get_falcon_status_by_code(code):
    http_status = HTTPStatus(code)
    return get_falcon_status(http_status)


class FalconRouter(BaseRouter):
    def __init__(self, app: falcon.asgi.App = None, **kwargs):
        self._resources = {}
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)
        if self.app is not None:
            resource = self._create_or_update_resource(path, method.upper(), endpoint)
            self.app.add_route(path, resource)

    def _create_or_update_resource(self, path: str, method: str, endpoint):
        resource = self._resources.get(path)
        if not resource:
            resource = type("DynamicResource", (), {})()
            self._resources[path] = resource
        method_name = METHODS_MAPPER[method]

        async def handle(req, resp, **path_params):
            await self._handle_request(endpoint, req, resp, **path_params)

        setattr(resource, method_name, handle)
        return resource

    async def _handle_request(self, endpoint, req, resp, **path_params):
        meta = getattr(endpoint, "__route_meta__", {})
        status_code = meta.get("status_code", 200)
        all_params = {**dict(req.params), **path_params}
        body = await self._read_body(req)
        try:
            kwargs = self.resolve_endpoint_params(endpoint, all_params, body)
        except Exception as e:
            error_response = self.handle_exception(e)
            resp.status = get_falcon_status_by_code(getattr(e, "status_code", 422))
            resp.media = error_response
            return
        try:
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)
        except Exception as e:
            error_response = self.handle_exception(e)
            resp.status = get_falcon_status_by_code(getattr(e, "status_code", 500))
            resp.media = error_response
            return
        resp.status = get_falcon_status(status_code)
        result = self._serialize_response(result)
        resp.media = result

    async def _read_body(self, req):
        try:
            body_bytes = await req.bounded_stream.read()
            if body_bytes:
                return json.loads(body_bytes.decode("utf-8"))
        except Exception:
            pass
        return {}

    # def _handle_request_error(self, resp, error_message: str):
    #     resp.status = falcon.HTTP_422
    #     resp.media = {"detail": error_message}
    #
    # def _handle_response_error(self, resp, error_message: str):
    #     resp.status = falcon.HTTP_500
    #     resp.media = {"detail": error_message}

    def _register_docs_endpoints(self):
        outer = self

        class OpenAPISchemaResource:
            async def on_get(inner_self, req, resp):
                resp.media = outer.openapi

        self.app.add_route(self.openapi_url, OpenAPISchemaResource())

        class SwaggerUIResource:
            async def on_get(inner_self, req, resp):
                html = outer.render_swagger_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        class RedocUIResource:
            async def on_get(inner_self, req, resp):
                html = outer.render_redoc_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        self.app.add_route(self.docs_url, SwaggerUIResource())
        self.app.add_route(self.redoc_url, RedocUIResource())
