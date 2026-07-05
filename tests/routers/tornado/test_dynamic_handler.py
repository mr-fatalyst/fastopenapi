import json
from unittest.mock import AsyncMock, MagicMock

import pytest
import tornado.web

from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.tornado.handler import TornadoDynamicHandler


class TestTornadoDynamicHandler:
    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.query_arguments = {}
        request.body = None
        return request

    @pytest.fixture
    def mock_application(self):
        return MagicMock()

    @pytest.fixture
    def mock_handler(self, mock_application, mock_request):
        handler = TornadoDynamicHandler(mock_application, mock_request)
        handler.endpoint = MagicMock()
        handler.router = MagicMock()
        handler.path_kwargs = {}

        # Mock these methods specifically
        handler.set_status = MagicMock()
        handler.set_header = MagicMock()
        handler.write = MagicMock()

        # Use AsyncMock for async methods to make them awaitable
        handler.finish = AsyncMock()

        return handler

    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_handler):
        http_error = tornado.web.HTTPError(404, "Not found")

        # tornado's exception path calls finish() synchronously and
        # discards the result, so an AsyncMock would leak a coroutine
        mock_handler.finish = MagicMock()

        mock_handler._handle_request_exception(http_error)

        mock_handler.set_status.assert_called_once_with(404, reason=None)
        args, kwargs = mock_handler.set_status.call_args
        assert args == (404,)

    @pytest.mark.asyncio
    async def test_applies_wire_triple(self, mock_handler):
        """The handler faithfully applies status, headers and body"""
        wire = WireResponse(
            body=b'{"key":"value"}',
            status=201,
            headers={"Content-Type": "application/json", "X-Custom": "yes"},
        )
        mock_handler.request.method = "GET"
        mock_handler.router.handle_request_async = AsyncMock(return_value=wire)

        await mock_handler.handle_request()

        mock_handler.set_status.assert_called_once_with(201)
        mock_handler.set_header.assert_any_call("Content-Type", "application/json")
        mock_handler.set_header.assert_any_call("X-Custom", "yes")
        mock_handler.write.assert_called_once_with(b'{"key":"value"}')
        mock_handler.finish.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_no_body_status_skips_write(self, mock_handler):
        """204/304 write no body but keep custom headers"""
        wire = WireResponse(body=None, status=304, headers={"ETag": '"e"'})
        mock_handler.request.method = "GET"
        mock_handler.router.handle_request_async = AsyncMock(return_value=wire)

        await mock_handler.handle_request()

        mock_handler.set_status.assert_called_once_with(304)
        mock_handler.set_header.assert_any_call("ETag", '"e"')
        mock_handler.write.assert_not_called()
        mock_handler.finish.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_head_request_skips_body(self, mock_handler):
        """HEAD runs the GET pipeline but never writes a body"""
        wire = WireResponse(
            body=b'{"key":"value"}',
            status=200,
            headers={"Content-Type": "application/json"},
        )
        mock_handler.request.method = "HEAD"
        mock_handler.endpoint = None
        mock_handler.endpoints = {"GET": MagicMock()}
        mock_handler.router.handle_request_async = AsyncMock(return_value=wire)

        await mock_handler.handle_request()

        mock_handler.set_status.assert_called_once_with(200)
        mock_handler.write.assert_not_called()
        mock_handler.finish.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_method_not_allowed_is_json_with_allow_header(self, mock_handler):
        """405 responses carry an Allow header and a JSON envelope"""
        mock_handler.request.method = "DELETE"
        mock_handler.endpoint = None
        mock_handler.endpoints = {"GET": MagicMock(), "POST": MagicMock()}

        await mock_handler.handle_request()

        mock_handler.set_status.assert_called_once_with(405)
        mock_handler.set_header.assert_any_call("Allow", "GET, HEAD, POST")
        mock_handler.set_header.assert_any_call("Content-Type", "application/json")
        body = mock_handler.write.call_args[0][0]
        error = json.loads(body)["error"]
        assert error["status"] == 405
        assert error["type"] == "method_not_allowed"

    @pytest.mark.asyncio
    async def test_none_body_on_regular_status_skips_write(self, mock_handler):
        wire = WireResponse(body=None, status=200, headers={})
        mock_handler.request.method = "GET"
        mock_handler.router.handle_request_async = AsyncMock(return_value=wire)

        await mock_handler.handle_request()

        mock_handler.set_status.assert_called_once_with(200)
        mock_handler.write.assert_not_called()
        mock_handler.finish.assert_called_once_with()


class TestTornado405WithoutGet:
    @pytest.fixture
    def handler(self):
        h = TornadoDynamicHandler(MagicMock(), MagicMock())
        h.router = MagicMock()
        h.path_kwargs = {}
        h.set_status = MagicMock()
        h.set_header = MagicMock()
        h.write = MagicMock()
        h.finish = AsyncMock()
        return h

    @pytest.mark.asyncio
    async def test_allow_header_without_head_when_no_get(self, handler):
        """Allow lists only real methods when the route has no GET"""
        handler.request.method = "DELETE"
        handler.endpoint = None
        handler.endpoints = {"POST": MagicMock()}

        await handler.handle_request()

        handler.set_status.assert_called_once_with(405)
        handler.set_header.assert_any_call("Allow", "POST")
