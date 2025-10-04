import json
from io import BytesIO
from unittest.mock import Mock

import pytest
from quart import Quart, request

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.quart.extractors import QuartRequestDataExtractor


class TestQuartRequestDataExtractor:

    @staticmethod
    def create_app():
        """Helper to create Quart app for testing"""
        return Quart(__name__)

    @pytest.mark.asyncio
    async def test_get_path_params(self):
        """Test path parameters extraction"""
        app = self.create_app()

        async with app.test_request_context("/users/123/posts/test"):
            request.path_params = {"id": "123", "slug": "test"}

            result = QuartRequestDataExtractor._get_path_params(request)

            assert result == {"id": "123", "slug": "test"}

    @pytest.mark.asyncio
    async def test_get_path_params_missing(self):
        """Test missing path parameters"""
        app = self.create_app()

        async with app.test_request_context("/"):
            result = QuartRequestDataExtractor._get_path_params(request)

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        app = self.create_app()

        async with app.test_request_context("/?param1=value1&param2=value2"):
            result = QuartRequestDataExtractor._get_query_params(request)

            assert result == {"param1": "value1", "param2": "value2"}

    @pytest.mark.asyncio
    async def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        app = self.create_app()

        async with app.test_request_context("/?tags=tag1&tags=tag2"):
            result = QuartRequestDataExtractor._get_query_params(request)

            assert result == {"tags": ["tag1", "tag2"]}

    @pytest.mark.asyncio
    async def test_get_headers(self):
        """Test headers extraction"""
        app = self.create_app()

        async with app.test_request_context(
            "/",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer token",
            },
        ):
            result = QuartRequestDataExtractor._get_headers(request)

            assert result["Content-Type"] == "application/json"
            assert result["Authorization"] == "Bearer token"

    @pytest.mark.asyncio
    async def test_get_cookies(self):
        """Test cookies extraction"""
        app = self.create_app()

        async with app.test_request_context(
            "/", headers={"Cookie": "session=abc123; csrf=token456"}
        ):
            result = QuartRequestDataExtractor._get_cookies(request)

            assert result == {"session": "abc123", "csrf": "token456"}

    @pytest.mark.asyncio
    async def test_get_body_json(self):
        """Test JSON body extraction"""
        app = self.create_app()

        body_data = {"key": "value"}
        async with app.test_request_context(
            "/",
            method="POST",
            data=json.dumps(body_data),
            headers={"Content-Type": "application/json"},
        ):
            result = await QuartRequestDataExtractor._get_body(request)

            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_body_json_none(self):
        """Test JSON body returning None"""
        app = self.create_app()

        async with app.test_request_context(
            "/", method="POST", data="", headers={"Content-Type": "application/json"}
        ):
            result = await QuartRequestDataExtractor._get_body(request)

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_non_json(self):
        """Test non-JSON body"""
        app = self.create_app()

        async with app.test_request_context(
            "/",
            method="POST",
            data="plain text",
            headers={"Content-Type": "text/plain"},
        ):
            result = await QuartRequestDataExtractor._get_body(request)

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_body_no_mimetype(self):
        """Test body with no mimetype"""
        app = self.create_app()

        async with app.test_request_context("/", method="POST"):
            result = await QuartRequestDataExtractor._get_body(request)

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_form_data(self):
        """Test form data extraction"""
        app = self.create_app()

        async with app.test_request_context(
            "/",
            method="POST",
            form={"field1": "value1", "field2": "value2"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ):
            result = await QuartRequestDataExtractor._get_form_data(request)

            assert result == {"field1": "value1", "field2": "value2"}

    @pytest.mark.asyncio
    async def test_get_files(self):
        """Test files extraction"""
        app = self.create_app()

        async with app.test_request_context(
            "/",
            method="POST",
            form={"upload": (BytesIO(b"file content"), "test.txt")},
            headers={"Content-Type": "multipart/form-data"},
        ):
            result = await QuartRequestDataExtractor._get_files(request)

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full request data extraction"""
        app = self.create_app()

        body_data = {"data": "test"}
        async with app.test_request_context(
            "/?param=value",
            method="POST",
            data=json.dumps(body_data),
            headers={"Content-Type": "application/json", "Cookie": "session=abc"},
        ):
            request.path_params = {"id": "123"}

            env = RequestEnvelope(request=request, path_params=None)

            result = await QuartRequestDataExtractor.extract_request_data(env)

            assert isinstance(result, RequestData)
            assert result.path_params == {"id": "123"}
            assert result.query_params == {"param": "value"}
            assert "content-type" in result.headers or "Content-Type" in result.headers
            assert result.cookies == {"session": "abc"}
            assert result.body == {"data": "test"}

    @pytest.mark.asyncio
    async def test_get_files_attribute_error(self):
        """Test files extraction when request.files raises AttributeError"""
        app = self.create_app()

        async with app.test_request_context("/"):

            original_files = request.files
            delattr(request.__class__, "files")

            try:
                result = await QuartRequestDataExtractor._get_files(request)
                assert result == {}
            finally:
                request.__class__.files = original_files

    @pytest.mark.asyncio
    async def test_get_files_runtime_error(self):
        """Test files extraction when request.files raises RuntimeError"""
        app = self.create_app()

        async with app.test_request_context("/"):

            def raise_runtime_error():
                raise RuntimeError("Async context error")

            type(request).files = property(lambda self: raise_runtime_error())

            result = await QuartRequestDataExtractor._get_files(request)

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_files_single_file(self):
        """Test extraction of single file"""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        mock_storage = Mock()
        mock_storage.keys = Mock(return_value=["upload"])
        mock_storage.getlist = Mock(return_value=[mock_file])

        request = Mock()

        async def mock_files_coroutine():
            return mock_storage

        request.files = mock_files_coroutine()

        result = await QuartRequestDataExtractor._get_files(request)

        assert "upload" in result
        assert not isinstance(result["upload"], list)
        assert result["upload"].filename == "test.txt"

    @pytest.mark.asyncio
    async def test_get_files_multiple_same_name(self):
        """Test extraction of multiple files with same field name"""
        from unittest.mock import Mock

        mock_file1 = Mock()
        mock_file1.filename = "file1.txt"
        mock_file1.content_type = "text/plain"

        mock_file2 = Mock()
        mock_file2.filename = "file2.txt"
        mock_file2.content_type = "text/plain"

        mock_file3 = Mock()
        mock_file3.filename = "file3.txt"
        mock_file3.content_type = "text/plain"

        mock_storage = Mock()
        mock_storage.keys = Mock(return_value=["uploads"])
        mock_storage.getlist = Mock(return_value=[mock_file1, mock_file2, mock_file3])

        request = Mock()

        async def mock_files_coroutine():
            return mock_storage

        request.files = mock_files_coroutine()

        result = await QuartRequestDataExtractor._get_files(request)

        assert "uploads" in result
        assert isinstance(result["uploads"], list)
        assert len(result["uploads"]) == 3
        assert result["uploads"][0].filename == "file1.txt"
        assert result["uploads"][1].filename == "file2.txt"
        assert result["uploads"][2].filename == "file3.txt"

    @pytest.mark.asyncio
    async def test_get_files_filename_unknown(self):
        """Test file upload without filename defaults to 'unknown'"""
        from unittest.mock import Mock

        mock_file = Mock()
        mock_file.filename = None
        mock_file.content_type = "application/octet-stream"

        mock_storage = Mock()
        mock_storage.keys = Mock(return_value=["file"])
        mock_storage.getlist = Mock(return_value=[mock_file])

        request = Mock()

        async def mock_files_coroutine():
            return mock_storage

        request.files = mock_files_coroutine()

        result = await QuartRequestDataExtractor._get_files(request)

        assert "file" in result
        assert result["file"].filename == "unknown"
