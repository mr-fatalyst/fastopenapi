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
        part1.filename = None
        part1.text = AsyncMock(return_value="value1")

        part2 = Mock()
        part2.name = "field2"
        part2.filename = None
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
        request = AsyncMock(return_value=Mock())
        request.content_type = "application/x-www-form-urlencoded"

        result = await AioHttpRequestDataExtractor._get_form_data(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data_urlencoded_with_getall(self):
        """Test form data extraction with getall method"""
        request = Mock()
        request.content_type = "application/x-www-form-urlencoded"

        post_data = Mock()
        post_data.__iter__ = Mock(return_value=iter(["field1", "field2", "tags"]))
        post_data.getall = Mock(
            side_effect=lambda k: (
                ["value1"]
                if k == "field1"
                else ["value2"] if k == "field2" else ["tag1", "tag2"]
            )
        )

        request.post = AsyncMock(return_value=post_data)

        result = await AioHttpRequestDataExtractor._get_form_data(request)

        assert result == {
            "field1": "value1",
            "field2": "value2",
            "tags": ["tag1", "tag2"],
        }

    @pytest.mark.asyncio
    async def test_get_files_multiple_files_same_name(self):
        """Test extraction of multiple files with the same field name"""
        request = Mock()
        request.content_type = "multipart/form-data"

        async def create_multipart_reader():
            file_part1 = Mock()
            file_part1.name = "upload"
            file_part1.filename = "file1.txt"
            file_part1.headers = {"Content-Type": "text/plain"}
            file_part1.read = AsyncMock(return_value=b"content 1")

            file_part2 = Mock()
            file_part2.name = "upload"
            file_part2.filename = "file2.txt"
            file_part2.headers = {"Content-Type": "text/plain"}
            file_part2.read = AsyncMock(return_value=b"content 2")

            file_part3 = Mock()
            file_part3.name = "upload"
            file_part3.filename = "file3.txt"
            file_part3.headers = {"Content-Type": "text/plain"}
            file_part3.read = AsyncMock(return_value=b"content 3")

            async def gen():
                yield file_part1
                yield file_part2
                yield file_part3

            return gen()

        request.multipart = AsyncMock(side_effect=create_multipart_reader)

        result = await AioHttpRequestDataExtractor._get_files(request)

        assert "upload" in result
        assert isinstance(result["upload"], list)
        assert len(result["upload"]) == 3
        assert result["upload"][0].filename == "file1.txt"
        assert result["upload"][1].filename == "file2.txt"
        assert result["upload"][2].filename == "file3.txt"

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = await AioHttpRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction with both form data and files"""
        request = Mock()
        request.match_info = {"id": "123"}
        request.query = Mock()
        request.query.__iter__ = Mock(return_value=iter(["param"]))
        request.query.getall = Mock(return_value=["value"])
        request.headers = {"Content-Type": "multipart/form-data"}
        request.cookies = {"session": "abc"}
        request.read = AsyncMock(return_value=b"")
        request.content_type = "multipart/form-data"

        async def create_multipart_reader():
            # Mock form field (without filename)
            form_part = Mock()
            form_part.name = "field"
            form_part.filename = None
            form_part.text = AsyncMock(return_value="value")

            # Mock file part (with filename)
            file_part = Mock()
            file_part.name = "upload"
            file_part.filename = "test.txt"
            file_part.headers = {"Content-Type": "text/plain"}
            file_part.read = AsyncMock(return_value=b"file content")

            async def gen():
                yield form_part
                yield file_part

            return gen()

        request.multipart = AsyncMock(side_effect=create_multipart_reader)

        env = RequestEnvelope(request=request, path_params=None)

        result = await AioHttpRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "multipart/form-data"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {}
        assert result.form_data == {"field": "value"}
        assert "upload" in result.files
        assert result.files["upload"].filename == "test.txt"

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
