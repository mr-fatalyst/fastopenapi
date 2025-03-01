import inspect
import json

import falcon.asgi
from pydantic import BaseModel

from fastopenapi.base_router import BaseRouter

METHODS_MAPPER = {
    "GET": "on_get",
    "POST": "on_post",
    "PUT": "on_put",
    "PATCH": "on_patch",
    "DELETE": "on_delete",
}


class FalconRouter(BaseRouter):
    def __init__(
        self,
        app: falcon.asgi.App = None,
        docs_url: str = "/docs/",
        openapi_version: str = "3.0.0",
        title: str = "My Falcon App",
        version: str = "0.1.0",
    ):
        super().__init__(app, docs_url, openapi_version, title, version)
        if self.app is not None:
            self._register_docs_endpoints()

    def add_route(self, path: str, method: str, endpoint):
        super().add_route(path, method, endpoint)
        if self.app is not None:
            resource = self._create_resource(endpoint, method.upper())
            self.app.add_route(path, resource)

    def include_router(self, other: BaseRouter):
        for path, method, endpoint in other.get_routes():
            self.add_route(path, method, endpoint)

    def _create_resource(self, endpoint, method: str):
        class Resource:
            async def handle(inner_self, req, resp):
                params = dict(req.params)
                try:
                    body_bytes = await req.bounded_stream.read()
                    if body_bytes:
                        body = json.loads(body_bytes.decode("utf-8"))
                        params.update(body)
                except Exception:
                    pass
                try:
                    if inspect.iscoroutinefunction(endpoint):
                        result = await endpoint(**params)
                    else:
                        result = endpoint(**params)
                except TypeError as exc:
                    resp.status = falcon.HTTP_422
                    resp.media = {"detail": str(exc)}
                    return
                if isinstance(result, BaseModel):
                    result = result.model_dump()
                resp.media = result

        res = Resource()
        setattr(res, METHODS_MAPPER[method], res.handle)
        return res

    def _register_docs_endpoints(self):
        outer = self

        class OpenAPISchemaResource:
            async def on_get(inner_self, req, resp):
                resp.media = outer.generate_openapi()

        self.app.add_route("/openapi.json", OpenAPISchemaResource())

        class SwaggerUIResource:
            async def on_get(inner_self, req, resp):
                html = outer.render_swagger_ui("/openapi.json")
                resp.content_type = "text/html"
                resp.text = html

        self.app.add_route(self.docs_url, SwaggerUIResource())
