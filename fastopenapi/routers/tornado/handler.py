from tornado.web import RequestHandler

from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.tornado.utils import json_encode


class TornadoDynamicHandler(RequestHandler):
    """Dynamic request handler for Tornado"""

    def initialize(self, **kwargs):
        self.endpoints = kwargs.get("endpoints", {})
        self.router = kwargs.get("router")

    async def prepare(self):
        """Prepare request data"""
        self.endpoint = self.endpoints.get(self.request.method.upper())

    def _set_response_headers(self, headers):
        """Set response headers from result"""
        content_type = headers.get("Content-Type")
        if content_type:
            self.set_header("Content-Type", content_type)

        for key, value in headers.items():
            if key.lower() != "content-type":
                self.set_header(key, value)

        return content_type

    async def _send_response(self, content, content_type, status_code):
        """Send response based on content type"""
        if status_code == 204:
            await self.finish()
            return

        # Binary content
        if isinstance(content, bytes):
            if not content_type:
                self.set_header("Content-Type", "application/octet-stream")
            await self.finish(content)

        # String non-JSON content
        elif isinstance(content, str) and content_type not in [
            "application/json",
            "text/json",
        ]:
            if not content_type:
                self.set_header("Content-Type", "text/plain")
            await self.finish(content)

        # JSON content
        else:
            if not content_type:
                self.set_header("Content-Type", "application/json")
            await self.finish(json_encode(content))

    async def handle_request(self):
        """Common request handling"""
        if not hasattr(self, "endpoint") or not self.endpoint:
            self.send_error(405)
            return

        env = RequestEnvelope(request=self.request, path_params=self.path_kwargs)
        result_response = await self.router.handle_request_async(self.endpoint, env)

        self.set_status(result_response.status_code)
        content_type = self._set_response_headers(result_response.headers)
        await self._send_response(
            result_response.content, content_type, result_response.status_code
        )

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
