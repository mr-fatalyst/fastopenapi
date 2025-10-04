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
        form_mock.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "field1" else ["value2"]
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
        request.files = Mock()
        request.files.keys = Mock(return_value=[])

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
        form_mock.getlist = Mock(return_value=["form_value"])
        request.form = form_mock

        request.files = Mock()
        request.files.keys = Mock(return_value=[])

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

    @pytest.mark.asyncio
    async def test_get_files_single_file(self):
        """Test files extraction with single file"""
        request = Mock()

        mock_file = Mock()
        mock_file.name = "photo.jpg"
        mock_file.type = "image/jpeg"
        mock_file.body = b"fake image data"

        files_mock = Mock()
        files_mock.keys = Mock(return_value=["avatar"])
        files_mock.getlist = Mock(return_value=[mock_file])
        request.files = files_mock

        result = await SanicRequestDataExtractor._get_files(request)

        assert "avatar" in result
        assert not isinstance(result["avatar"], list)
        assert result["avatar"].filename == "photo.jpg"
        assert result["avatar"].content_type == "image/jpeg"
        assert result["avatar"].size == 15

    @pytest.mark.asyncio
    async def test_get_files_multiple_files_same_key(self):
        """Test files extraction with multiple files for same key"""
        request = Mock()

        mock_files = []
        for i in range(1, 4):
            mock_file = Mock()
            mock_file.name = f"file{i}.pdf"
            mock_file.type = "application/pdf"
            mock_file.body = f"content{i}".encode()
            mock_files.append(mock_file)

        files_mock = Mock()
        files_mock.keys = Mock(return_value=["docs"])
        files_mock.getlist = Mock(return_value=mock_files)
        request.files = files_mock

        result = await SanicRequestDataExtractor._get_files(request)

        assert "docs" in result
        assert isinstance(result["docs"], list)
        assert len(result["docs"]) == 3
        assert result["docs"][0].filename == "file1.pdf"
        assert result["docs"][1].filename == "file2.pdf"
        assert result["docs"][2].filename == "file3.pdf"

    @pytest.mark.asyncio
    async def test_get_files_no_files_attr(self):
        """Test files extraction when request has no files attribute"""
        request = Mock(spec=[])  # Mock without files attribute

        result = await SanicRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files_empty_body(self):
        """Test files extraction when file body is None"""
        request = Mock()

        mock_file = Mock()
        mock_file.name = "empty.txt"
        mock_file.type = "text/plain"
        mock_file.body = None

        files_mock = Mock()
        files_mock.keys = Mock(return_value=["upload"])
        files_mock.getlist = Mock(return_value=[mock_file])
        request.files = files_mock

        result = await SanicRequestDataExtractor._get_files(request)

        assert "upload" in result
        assert result["upload"].size is None
        assert result["upload"].file is None

    @pytest.mark.asyncio
    async def test_get_files_empty_keys(self):
        """Test files extraction with empty files"""
        request = Mock()

        files_mock = Mock()
        files_mock.keys = Mock(return_value=[])
        request.files = files_mock

        result = await SanicRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files_multiple_keys(self):
        """Test files extraction with multiple different keys"""
        request = Mock()

        mock_avatar = Mock()
        mock_avatar.name = "avatar.jpg"
        mock_avatar.type = "image/jpeg"
        mock_avatar.body = b"avatar data"

        mock_doc = Mock()
        mock_doc.name = "document.pdf"
        mock_doc.type = "application/pdf"
        mock_doc.body = b"pdf data"

        files_mock = Mock()
        files_mock.keys = Mock(return_value=["avatar", "document"])
        files_mock.getlist = Mock(
            side_effect=lambda k: [mock_avatar] if k == "avatar" else [mock_doc]
        )
        request.files = files_mock

        result = await SanicRequestDataExtractor._get_files(request)

        assert len(result) == 2
        assert "avatar" in result
        assert "document" in result
        assert result["avatar"].filename == "avatar.jpg"
        assert result["document"].filename == "document.pdf"

    @pytest.mark.asyncio
    async def test_get_form_data_multiple_values(self):
        """Test form data with multiple values for same key"""
        request = Mock()
        form_mock = Mock()
        form_mock.__iter__ = Mock(return_value=iter(["tags"]))
        form_mock.getlist = Mock(return_value=["tag1", "tag2", "tag3"])

        request.form = form_mock

        result = await SanicRequestDataExtractor._get_form_data(request)

        assert result == {"tags": ["tag1", "tag2", "tag3"]}
