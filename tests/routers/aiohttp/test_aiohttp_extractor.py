from unittest.mock import AsyncMock, Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.aiohttp.extractors import AioHttpRequestDataExtractor
from fastopenapi.routers.common import RequestEnvelope


class TestAioHttpRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.match_info = {"id": "123", "name": "test"}

        result = AioHttpRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "name": "test"}

    def test_get_path_params_empty(self):
        """Test empty path parameters"""
        request = Mock()
        request.match_info = {}

        result = AioHttpRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        request.query = Mock()
        request.query.__iter__ = Mock(return_value=iter(["param1", "param2"]))
        request.query.getall = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["value2"]
        )

        result = AioHttpRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        request.query = Mock()
        request.query.__iter__ = Mock(return_value=iter(["tags"]))
        request.query.getall = Mock(return_value=["tag1", "tag2", "tag3"])

        result = AioHttpRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2", "tag3"]}

    def test_get_query_params_empty(self):
        """Test empty query parameters"""
        request = Mock()
        request.query = Mock()
        request.query.__iter__ = Mock(return_value=iter([]))

        result = AioHttpRequestDataExtractor._get_query_params(request)

        assert result == {}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = AioHttpRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_headers_empty(self):
        """Test empty headers"""
        request = Mock()
        request.headers = {}

        result = AioHttpRequestDataExtractor._get_headers(request)

        assert result == {}

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = AioHttpRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    def test_get_cookies_empty(self):
        """Test empty cookies"""
        request = Mock()
        request.cookies = {}

        result = AioHttpRequestDataExtractor._get_cookies(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.read = AsyncMock(return_value=b'{"key": "value"}')
        request.json = AsyncMock(return_value={"key": "value"})

        result = await AioHttpRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}
        request.read.assert_called_once()
        request.json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_body_empty(self):
        """Test empty body"""
        request = Mock()
        request.read = AsyncMock(return_value=b"")

        result = await AioHttpRequestDataExtractor._get_body(request)

        assert result == {}
        request.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_body_json_error(self):
        """Test body with JSON parsing error"""
        request = Mock()
        request.read = AsyncMock(return_value=b'{"invalid": json}')
        request.json = AsyncMock(side_effect=Exception("Invalid JSON"))

        result = await AioHttpRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data_multipart(self):
        """Test multipart form data extraction"""
        request = Mock()
        request.content_type = "multipart/form-data"

        part1 = Mock()
        part1.name = "field1"
        part1.text = AsyncMock(return_value="value1")

        part2 = Mock()
        part2.name = "field2"
        part2.text = AsyncMock(return_value="value2")

        async def mock_multipart_reader():
            for part in [part1, part2]:
                yield part

        request.multipart = AsyncMock(return_value=mock_multipart_reader())

        result = await AioHttpRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    @pytest.mark.asyncio
    async def test_get_form_data_non_multipart(self):
        """Test non-multipart form data"""
        request = Mock()
        request.content_type = "application/x-www-form-urlencoded"

        result = await AioHttpRequestDataExtractor._get_form_data(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = await AioHttpRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.match_info = {"id": "123"}
        request.query = Mock()
        request.query.__iter__ = Mock(return_value=iter(["param"]))
        request.query.getall = Mock(return_value=["value"])
        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.read = AsyncMock(return_value=b'{"data": "test"}')
        request.json = AsyncMock(return_value={"data": "test"})
        request.content_type = "application/json"

        env = RequestEnvelope(request=request, path_params=None)

        result = await AioHttpRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}  # normalized
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {}
        assert result.files == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_with_provided_path_params(self):
        """Test extraction with pre-provided path params"""
        request = Mock()
        request.query = Mock()
        request.query.__iter__ = Mock(return_value=iter([]))
        request.headers = {}
        request.cookies = {}
        request.read = AsyncMock(return_value=b"")
        request.content_type = "application/json"

        env = RequestEnvelope(request=request, path_params={"provided": "param"})

        result = await AioHttpRequestDataExtractor.extract_request_data(env)

        assert result.path_params == {"provided": "param"}
