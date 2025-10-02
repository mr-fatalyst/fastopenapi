from unittest.mock import AsyncMock, MagicMock

import pytest
import tornado.web

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

        mock_handler._handle_request_exception(http_error)

        mock_handler.set_status.assert_called_once_with(404, reason=None)
        args, kwargs = mock_handler.set_status.call_args
        assert args == (404,)
