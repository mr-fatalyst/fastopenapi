from unittest.mock import AsyncMock, MagicMock

import pytest
import tornado.web
from pydantic_core import to_json

from fastopenapi.routers.tornado import TornadoDynamicHandler


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
    async def test_prepare_method(self, mock_handler):
        # Empty body
        mock_handler.request.body = None
        await mock_handler.prepare()
        assert not hasattr(mock_handler, "json_body") or mock_handler.json_body == {}

        # Valid JSON body
        mock_handler.request.body = to_json({"name": "Test"}).decode("utf-8")
        await mock_handler.prepare()
        assert hasattr(mock_handler, "json_body")
        assert mock_handler.json_body == {"name": "Test"}

        # Invalid JSON body
        mock_handler.request.body = b"not-json"
        await mock_handler.prepare()
        assert hasattr(mock_handler, "json_body")
        assert mock_handler.json_body == {}

    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_handler):
        http_error = tornado.web.HTTPError(404, "Not found")

        await mock_handler.handle_http_exception(http_error)

        mock_handler.set_status.assert_called_once_with(404)
        mock_handler.finish.assert_called_once()
