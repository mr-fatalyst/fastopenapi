from unittest.mock import Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.tornado.extractors import TornadoRequestDataExtractor


class TestTornadoRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_kwargs = {"id": "123", "slug": "test"}

        result = TornadoRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_none(self):
        """Test path parameters when None"""
        request = Mock()
        request.path_kwargs = None

        result = TornadoRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        query_args_mock = Mock()
        query_args_mock.__iter__ = Mock(return_value=iter(["param1", "param2"]))
        query_args_mock.__getitem__ = Mock(
            side_effect=lambda k: [b"value1"] if k == "param1" else [b"value2"]
        )
        request.query_arguments = query_args_mock

        result = TornadoRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        query_args_mock = Mock()
        query_args_mock.__iter__ = Mock(return_value=iter(["tags"]))
        query_args_mock.__getitem__ = Mock(return_value=[b"tag1", b"tag2"])
        request.query_arguments = query_args_mock

        result = TornadoRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2"]}

    def test_get_query_params_empty(self):
        """Test empty query parameters"""
        request = Mock()
        query_args_mock = Mock()
        query_args_mock.__iter__ = Mock(return_value=iter([]))
        request.query_arguments = query_args_mock

        result = TornadoRequestDataExtractor._get_query_params(request)

        assert result == {}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = TornadoRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = TornadoRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.body = b'{"key": "value"}'

        result = await TornadoRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_body_empty(self):
        """Test empty body"""
        request = Mock()
        request.body = b""

        result = await TornadoRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_none(self):
        """Test None body"""
        request = Mock()
        request.body = None

        result = await TornadoRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_json_error(self):
        """Test JSON parsing error"""
        request = Mock()
        request.body = b'{"invalid": json}'

        result = await TornadoRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data(self):
        """Test form data extraction"""
        request = Mock()
        body_args_mock = Mock()
        body_args_mock.items = Mock(
            return_value=[("field1", [b"value1"]), ("field2", [b"value2"])]
        )
        request.body_arguments = body_args_mock

        result = await TornadoRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    @pytest.mark.asyncio
    async def test_get_form_data_multiple_values(self):
        """Test form data with multiple values"""
        request = Mock()
        body_args_mock = Mock()
        body_args_mock.items = Mock(return_value=[("tags", [b"tag1", b"tag2"])])
        request.body_arguments = body_args_mock

        result = await TornadoRequestDataExtractor._get_form_data(request)

        assert result == {"tags": ["tag1", "tag2"]}

    @pytest.mark.asyncio
    async def test_get_form_data_none(self):
        """Test form data when None"""
        request = Mock()
        request.body_arguments = None

        result = await TornadoRequestDataExtractor._get_form_data(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = await TornadoRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.path_kwargs = {"id": "123"}

        query_args_mock = Mock()
        query_args_mock.__iter__ = Mock(return_value=iter(["param"]))
        query_args_mock.__getitem__ = Mock(return_value=[b"value"])
        request.query_arguments = query_args_mock

        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.body = b'{"data": "test"}'

        body_args_mock = Mock()
        body_args_mock.items = Mock(return_value=[("form_field", [b"form_value"])])
        request.body_arguments = body_args_mock

        env = RequestEnvelope(request=request, path_params=None)

        result = await TornadoRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
