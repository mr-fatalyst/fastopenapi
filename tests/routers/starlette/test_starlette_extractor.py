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
        request.headers = Mock()
        request.headers.get = Mock(return_value="application/json")

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

    @pytest.mark.asyncio
    async def test_get_form_data_skip_files(self):
        """Test that files are skipped in form data extraction"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data; boundary=something")
        request.headers = headers_mock

        # Mock file with filename attribute
        mock_file = Mock()
        mock_file.filename = "photo.jpg"

        form_mock = Mock()
        form_mock.items = Mock(
            return_value=[
                ("username", "john"),
                ("avatar", mock_file),  # This should be skipped
                ("email", "john@example.com"),
            ]
        )
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_form_data(request)

        # Only non-file fields should be present
        assert result == {"username": "john", "email": "john@example.com"}
        assert "avatar" not in result

    @pytest.mark.asyncio
    async def test_get_files_single_file(self):
        """Test files extraction with single file"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data")
        request.headers = headers_mock

        mock_file = Mock()
        mock_file.filename = "photo.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 1024

        form_mock = Mock()
        form_mock.items = Mock(return_value=[("avatar", mock_file)])
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_files(request)

        assert "avatar" in result
        assert not isinstance(result["avatar"], list)
        assert result["avatar"].filename == "photo.jpg"
        assert result["avatar"].content_type == "image/jpeg"
        assert result["avatar"].size == 1024

    @pytest.mark.asyncio
    async def test_get_files_multiple_files_same_key(self):
        """Test files extraction with multiple files for same key"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data")
        request.headers = headers_mock

        mock_file1 = Mock()
        mock_file1.filename = "file1.pdf"
        mock_file1.content_type = "application/pdf"
        mock_file1.size = 500

        mock_file2 = Mock()
        mock_file2.filename = "file2.pdf"
        mock_file2.content_type = "application/pdf"
        mock_file2.size = 600

        mock_file3 = Mock()
        mock_file3.filename = "file3.pdf"
        mock_file3.content_type = "application/pdf"
        mock_file3.size = 700

        form_mock = Mock()
        form_mock.items = Mock(
            return_value=[
                ("docs", mock_file1),
                ("docs", mock_file2),
                ("docs", mock_file3),
            ]
        )
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_files(request)

        assert "docs" in result
        assert isinstance(result["docs"], list)
        assert len(result["docs"]) == 3
        assert result["docs"][0].filename == "file1.pdf"
        assert result["docs"][1].filename == "file2.pdf"
        assert result["docs"][2].filename == "file3.pdf"

    @pytest.mark.asyncio
    async def test_get_files_without_size_attr(self):
        """Test files extraction when file object has no size attribute"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data")
        request.headers = headers_mock

        mock_file = Mock(spec=["filename", "content_type"])  # No size attribute
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        form_mock = Mock()
        form_mock.items = Mock(return_value=[("upload", mock_file)])
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_files(request)

        assert "upload" in result
        assert result["upload"].size is None

    @pytest.mark.asyncio
    async def test_get_files_non_multipart(self):
        """Test files extraction with non-multipart content type"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="application/json")
        request.headers = headers_mock

        result = await StarletteRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_files_mixed_form_data(self):
        """Test files extraction skips non-file form fields"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data")
        request.headers = headers_mock

        mock_file = Mock()
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 2048

        # Mock regular field without filename attribute
        mock_field = Mock(spec=[])  # No filename attribute

        form_mock = Mock()
        form_mock.items = Mock(
            return_value=[
                ("title", mock_field),
                ("document", mock_file),
                ("description", mock_field),
            ]
        )
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_files(request)

        # Only file should be extracted
        assert len(result) == 1
        assert "document" in result
        assert result["document"].filename == "document.pdf"

    @pytest.mark.asyncio
    async def test_get_files_empty_form(self):
        """Test files extraction with empty form"""
        request = Mock()
        headers_mock = Mock()
        headers_mock.get = Mock(return_value="multipart/form-data")
        request.headers = headers_mock

        form_mock = Mock()
        form_mock.items = Mock(return_value=[])
        request.form = AsyncMock(return_value=form_mock)

        result = await StarletteRequestDataExtractor._get_files(request)

        assert result == {}
