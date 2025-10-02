from unittest.mock import Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.sanic.extractors import SanicRequestDataExtractor


class TestSanicRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_params = {"id": "123", "slug": "test"}

        result = SanicRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing(self):
        """Test missing path parameters"""
        request = Mock(spec=[])

        result = SanicRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        args_mock = Mock()
        args_mock.items = Mock(
            return_value=[("param1", ["value1"]), ("param2", ["value2"])]
        )
        args_mock.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["value2"]
        )
        request.args = args_mock

        result = SanicRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        args_mock = Mock()
        args_mock.items = Mock(return_value=[("tags", ["tag1", "tag2"])])
        args_mock.getlist = Mock(return_value=["tag1", "tag2"])
        request.args = args_mock

        result = SanicRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2"]}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = SanicRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = SanicRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.json = {"key": "value"}

        result = await SanicRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_body_none(self):
        """Test empty JSON body"""
        request = Mock()
        request.json = None

        result = await SanicRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data(self):
        """Test form data extraction"""
        request = Mock()
        form_mock = Mock()
        form_mock.__iter__ = Mock(return_value=iter(["field1", "field2"]))
        form_mock.get = Mock(
            side_effect=lambda k: "value1" if k == "field1" else "value2"
        )
        request.form = form_mock

        result = await SanicRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    @pytest.mark.asyncio
    async def test_get_form_data_no_form_attr(self):
        """Test form data with no form attribute"""
        request = Mock(spec=["json"])

        result = await SanicRequestDataExtractor._get_form_data(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = await SanicRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.path_params = {"id": "123"}

        args_mock = Mock()
        args_mock.items = Mock(return_value=[("param", ["value"])])
        args_mock.getlist = Mock(return_value=["value"])
        request.args = args_mock

        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.json = {"data": "test"}

        form_mock = Mock()
        form_mock.__iter__ = Mock(return_value=iter(["form_field"]))
        form_mock.get = Mock(return_value="form_value")
        request.form = form_mock

        env = RequestEnvelope(request=request, path_params=None)

        result = await SanicRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
