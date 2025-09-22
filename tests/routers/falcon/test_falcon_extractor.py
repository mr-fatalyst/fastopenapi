import io
from unittest.mock import AsyncMock, Mock

import pytest

from fastopenapi.routers.falcon.extractors import (
    FalconAsyncRequestDataExtractor,
    FalconRequestDataExtractor,
)


class TestFalconRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_params = {"id": "123", "slug": "test"}

        result = FalconRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing(self):
        """Test missing path parameters"""
        request = Mock(spec=[])

        result = FalconRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_with_getall(self):
        """Test query parameters with getall method"""
        request = Mock()
        request.params = Mock()
        request.params.keys = Mock(return_value=["param1", "tags"])
        request.params.getall = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["tag1", "tag2"]
        )

        result = FalconRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "tags": ["tag1", "tag2"]}

    def test_get_query_params_without_getall(self):
        """Test query parameters without getall method"""
        request = Mock()
        request.params = Mock()
        request.params.keys = Mock(return_value=["param1", "param2"])
        request.params.get = Mock(
            side_effect=lambda k: "value1" if k == "param1" else "value2"
        )
        # Simulate no getall method
        del request.params.getall

        result = FalconRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = FalconRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = FalconRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.content_type = "application/json"
        request.bounded_stream = Mock()
        request.bounded_stream.read = Mock(return_value=b'{"key": "value"}')

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    def test_get_body_non_json(self):
        """Test non-JSON body"""
        request = Mock()
        request.content_type = "text/plain"

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_json_error(self):
        """Test JSON parsing error"""
        request = Mock()
        request.content_type = "application/json"
        request.bounded_stream = Mock()
        request.bounded_stream.read = Mock(return_value=b'{"invalid": json}')

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_empty(self):
        """Test empty JSON body"""
        request = Mock()
        request.content_type = "application/json"
        request.bounded_stream = Mock()
        request.bounded_stream.read = Mock(return_value=b"")

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_form_data(self):
        """Test form data extraction"""
        request = Mock()

        result = FalconRequestDataExtractor._get_form_data(request)

        assert result == {}

    def test_get_files_with_files_attr(self):
        """Test files extraction with files attribute"""
        request = Mock()

        file_mock = Mock()
        file_stream = io.BytesIO(b"file content")
        file_mock.stream = file_stream

        request.files = {"upload": file_mock}

        result = FalconRequestDataExtractor._get_files(request)

        assert result == {"upload": b"file content"}

    def test_get_files_no_files_attr(self):
        """Test files extraction without files attribute"""
        request = Mock(spec=[])

        result = FalconRequestDataExtractor._get_files(request)

        assert result == {}


class TestFalconAsyncRequestDataExtractor:

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test async JSON body extraction"""
        request = Mock()
        request.content_type = "application/json"
        request.bounded_stream = Mock()
        request.bounded_stream.read = AsyncMock(return_value=b'{"key": "value"}')

        result = await FalconAsyncRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_body_non_json(self):
        """Test async non-JSON body"""
        request = Mock()
        request.content_type = "text/plain"

        result = await FalconAsyncRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_json_error(self):
        """Test async JSON parsing error"""
        request = Mock()
        request.content_type = "application/json"
        request.bounded_stream = Mock()
        request.bounded_stream.read = AsyncMock(return_value=b'{"invalid": json}')

        result = await FalconAsyncRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data_calls_sync(self):
        """Test async form data calls sync method"""
        request = Mock()

        result = await FalconAsyncRequestDataExtractor._get_form_data(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files_calls_sync(self):
        """Test async files calls sync method"""
        request = Mock()
        request.files = {}

        result = await FalconAsyncRequestDataExtractor._get_files(request)

        assert result == {}
