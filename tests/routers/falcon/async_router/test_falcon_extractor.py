from unittest.mock import AsyncMock, Mock

import pytest

from fastopenapi.routers.falcon.extractors import FalconAsyncRequestDataExtractor


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
