from typing import Any

from tornado.web import RequestHandler

from fastopenapi.response.serializer import NO_BODY_STATUSES
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.tornado.utils import json_encode


class TornadoDynamicHandler(RequestHandler):
    """Dynamic request handler for Tornado"""

    endpoints: dict[str, Any]
    router: Any
    endpoint: Any

    def initialize(self, **kwargs: Any) -> None:
        self.endpoints = kwargs.get("endpoints", {})
        self.router = kwargs.get("router")

    async def prepare(self) -> None:
        """Prepare request data"""
        self.endpoint = self.endpoints.get((self.request.method or "").upper())

    async def handle_request(self) -> None:
        """Common request handling"""
        method = (self.request.method or "").upper()
        endpoint = getattr(self, "endpoint", None)
        if endpoint is None and method == "HEAD":
            # Auto-HEAD: serve HEAD from the GET pipeline
            endpoint = self.endpoints.get("GET")
        if endpoint is None:
            self._send_method_not_allowed()
            return

        env = RequestEnvelope(request=self.request, path_params=self.path_kwargs)
        wire = await self.router.handle_request_async(endpoint, env)

        self.set_status(wire.status)
        for key, value in wire.headers.items():
            self.set_header(key, value)

        no_body = wire.status in NO_BODY_STATUSES or method == "HEAD"
        if wire.body is not None and not no_body:
            self.write(wire.body)
        await self.finish()

    def _send_method_not_allowed(self) -> None:
        """JSON 405 with an Allow header instead of tornado's HTML page"""
        allowed = set(self.endpoints)
        if "GET" in allowed:
            allowed.add("HEAD")
        self.set_status(405)
        self.set_header("Allow", ", ".join(sorted(allowed)))
        self.set_header("Content-Type", "application/json")
        self.write(
            json_encode(
                {
                    "error": {
                        "type": "method_not_allowed",
                        "message": "Method Not Allowed",
                        "status": 405,
                    }
                }
            )
        )

    async def get(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()

    async def post(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()

    async def put(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()

    async def patch(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()

    async def head(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()

    async def options(self, *args: Any, **kwargs: Any) -> None:
        await self.handle_request()
