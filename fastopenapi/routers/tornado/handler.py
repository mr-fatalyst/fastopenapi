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

    async def handle_request(self):
        """Common request handling"""
        if not hasattr(self, "endpoint") or not self.endpoint:
            self.send_error(405)
            return

        env = RequestEnvelope(request=self.request, path_params=self.path_kwargs)
        result_response = await self.router.handle_request_async(self.endpoint, env)

        self.set_status(result_response.status_code)
        self.set_header("Content-Type", "application/json")

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
