from unittest.mock import AsyncMock, Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.starlette.extractors import StarletteRequestDataExtractor


class TestStarletteRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_params = {"id": "123", "slug": "test"}

        result = StarletteRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        request.query_params = Mock()
        request.query_params.__iter__ = Mock(return_value=iter(["param1", "param2"]))
        request.query_params.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["value2"]
        )

        result = StarletteRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        request.query_params = Mock()
        request.query_params.__iter__ = Mock(return_value=iter(["tags"]))
        request.query_params.getlist = Mock(return_value=["tag1", "tag2"])

        result = StarletteRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2"]}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = StarletteRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = StarletteRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.body = AsyncMock(return_value=b'{"key": "value"}')

        result = await StarletteRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_body_empty(self):
        """Test empty body"""
        request = Mock()
        request.body = AsyncMock(return_value=b"")

        result = await StarletteRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_json_error(self):
        """Test JSON parsing error"""
        request = Mock()
        request.body = AsyncMock(return_value=b'{"invalid": json}')

        result = await StarletteRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data_multipart(self):
        """Test multipart form data extraction"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data; boundary=something")
        request.headers = headers_mock

        form_mock = Mock()
        form_mock.items = Mock(
            return_value=[("field1", "value1"), ("field2", "value2")]
        )
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    @pytest.mark.asyncio
    async def test_get_form_data_non_multipart(self):
        """Test non-multipart form data"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="application/json")
        request.headers = headers_mock

        result = await StarletteRequestDataExtractor._get_form_data(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = await StarletteRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.path_params = {"id": "123"}
        request.query_params = Mock()
        request.query_params.__iter__ = Mock(return_value=iter(["param"]))
        request.query_params.getlist = Mock(return_value=["value"])

        class MockHeaders(dict):
            def get(self, key, default=None):
                return (
                    "multipart/form-data"
                    if key == "content-type"
                    else super().get(key, default)
                )

        request.headers = MockHeaders({"Content-Type": "application/json"})

        request.cookies = {"session": "abc"}
        request.body = AsyncMock(return_value=b'{"data": "test"}')

        form_mock = Mock()
        form_mock.items = Mock(return_value=[("form_field", "form_value")])
        request.form = AsyncMock(return_value=form_mock)

        env = RequestEnvelope(request=request, path_params=None)

        result = await StarletteRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
