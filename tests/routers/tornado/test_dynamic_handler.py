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

    @pytest.mark.asyncio
    async def test_binary_content_without_content_type(self, mock_handler):
        """Test binary content without explicit content type"""
        result_response = MagicMock()
        result_response.status_code = 200
        result_response.headers = {}  # No Content-Type
        result_response.content = b"binary data"

        mock_handler.router.handle_request_async = AsyncMock(
            return_value=result_response
        )

        await mock_handler.handle_request()

        # Should set default binary content type
        mock_handler.set_header.assert_any_call(
            "Content-Type", "application/octet-stream"
        )
        mock_handler.finish.assert_called_once_with(b"binary data")

    @pytest.mark.asyncio
    async def test_string_content_without_content_type(self, mock_handler):
        """Test string non-JSON content without explicit content type"""
        result_response = MagicMock()
        result_response.status_code = 200
        result_response.headers = {"Content-Type": "text/html"}  # Non-JSON type
        result_response.content = "<html>test</html>"

        mock_handler.router.handle_request_async = AsyncMock(
            return_value=result_response
        )

        await mock_handler.handle_request()

        mock_handler.set_header.assert_any_call("Content-Type", "text/html")
        mock_handler.finish.assert_called_once_with("<html>test</html>")

    @pytest.mark.asyncio
    async def test_string_plain_without_content_type(self, mock_handler):
        """Test plain string without content type header"""
        result_response = MagicMock()
        result_response.status_code = 200
        result_response.headers = {}  # No Content-Type
        result_response.content = "plain text"

        mock_handler.router.handle_request_async = AsyncMock(
            return_value=result_response
        )

        await mock_handler.handle_request()

        # Should set default text/plain
        mock_handler.set_header.assert_any_call("Content-Type", "text/plain")
        mock_handler.finish.assert_called_once_with("plain text")

    @pytest.mark.asyncio
    async def test_json_content_with_explicit_content_type(self, mock_handler):
        """Test JSON content with explicit content type already set"""
        result_response = MagicMock()
        result_response.status_code = 200
        result_response.headers = {"Content-Type": "application/json"}  # Already set
        result_response.content = {"key": "value"}

        mock_handler.router.handle_request_async = AsyncMock(
            return_value=result_response
        )

        await mock_handler.handle_request()

        # Should use existing content type, not set again
        mock_handler.set_header.assert_any_call("Content-Type", "application/json")
        # Verify it was called exactly once for Content-Type (from headers)
        content_type_calls = [
            call
            for call in mock_handler.set_header.call_args_list
            if call[0][0] == "Content-Type"
        ]
        assert len(content_type_calls) == 1

    @pytest.mark.asyncio
    async def test_json_content_without_content_type(self, mock_handler):
        """Test JSON content without explicit content type"""
        result_response = MagicMock()
        result_response.status_code = 200
        result_response.headers = {}  # No Content-Type
        result_response.content = {"key": "value"}

        mock_handler.router.handle_request_async = AsyncMock(
            return_value=result_response
        )

        await mock_handler.handle_request()

        # Should set default JSON content type
        mock_handler.set_header.assert_any_call("Content-Type", "application/json")
