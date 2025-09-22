from unittest.mock import AsyncMock, Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.quart.extractors import QuartRequestDataExtractor


class TestQuartRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_params = {"id": "123", "slug": "test"}

        result = QuartRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing(self):
        """Test missing path parameters"""
        request = Mock(spec=[])

        result = QuartRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        request.args = Mock()
        request.args.__iter__ = Mock(return_value=iter(["param1", "param2"]))
        request.args.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["value2"]
        )

        result = QuartRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        request.args = Mock()
        request.args.__iter__ = Mock(return_value=iter(["tags"]))
        request.args.getlist = Mock(return_value=["tag1", "tag2"])

        result = QuartRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2"]}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = QuartRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = QuartRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.mimetype = "application/json"
        request.get_json = AsyncMock(return_value={"key": "value"})

        result = await QuartRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}
        request.get_json.assert_called_once_with(silent=True)

    @pytest.mark.asyncio
    async def test_get_body_json_none(self):
        """Test JSON body returning None"""
        request = Mock()
        request.mimetype = "application/json"
        request.get_json = AsyncMock(return_value=None)

        result = await QuartRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_non_json(self):
        """Test non-JSON body"""
        request = Mock()
        request.mimetype = "text/plain"

        result = await QuartRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_no_mimetype(self):
        """Test body with no mimetype"""
        request = Mock()
        request.mimetype = None

        result = await QuartRequestDataExtractor._get_body(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data(self):
        """Test form data extraction"""
        request = Mock()

        form_mock = Mock()
        form_mock.__iter__ = Mock(return_value=iter(["field1", "field2"]))
        form_mock.__getitem__ = Mock(
            side_effect=lambda k: "value1" if k == "field1" else "value2"
        )

        async def mock_form():
            return form_mock

        request.form = mock_form()

        result = await QuartRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = await QuartRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.path_params = {"id": "123"}
        request.args = Mock()
        request.args.__iter__ = Mock(return_value=iter(["param"]))
        request.args.getlist = Mock(return_value=["value"])
        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.mimetype = "application/json"
        request.get_json = AsyncMock(return_value={"data": "test"})

        form_mock = Mock()
        form_mock.__iter__ = Mock(return_value=iter(["form_field"]))
        form_mock.__getitem__ = Mock(return_value="form_value")

        async def mock_form():
            return form_mock

        request.form = mock_form()

        env = RequestEnvelope(request=request, path_params=None)

        result = await QuartRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
