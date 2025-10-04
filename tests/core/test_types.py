import io
from unittest.mock import AsyncMock, Mock

import pytest

from fastopenapi.core.types import FileUpload, RequestData, Response


class TestFileUpload:

    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        file_obj = io.BytesIO(b"test content")
        upload = FileUpload(
            filename="test.txt", content_type="text/plain", size=1024, file=file_obj
        )

        assert upload.filename == "test.txt"
        assert upload.content_type == "text/plain"
        assert upload.size == 1024
        assert upload.file is file_obj

    def test_init_with_minimal_params(self):
        """Test initialization with minimal parameters"""
        upload = FileUpload(filename="test.txt")

        assert upload.filename == "test.txt"
        assert upload.content_type == "application/octet-stream"
        assert upload.size is None
        assert upload.file is None

    def test_file_property(self):
        """Test file property access"""
        file_obj = io.BytesIO(b"content")
        upload = FileUpload(filename="test.txt", file=file_obj)

        assert upload.file is file_obj

    def test_read_from_bytes(self):
        """Test read() with bytes object"""
        upload = FileUpload(filename="test.txt", file=b"test content")

        result = upload.read()

        assert result == b"test content"

    def test_read_from_file_like_object(self):
        """Test read() with file-like object returning bytes"""
        file_obj = io.BytesIO(b"file content")
        upload = FileUpload(filename="test.txt", file=file_obj)

        result = upload.read()

        assert result == b"file content"

    def test_read_from_file_returning_string(self):
        """Test read() with file-like object returning string"""
        file_obj = io.StringIO("string content")
        upload = FileUpload(filename="test.txt", file=file_obj)

        result = upload.read()

        assert result == b"string content"

    def test_read_no_read_method(self):
        """Test read() raises error when file has no read method"""
        upload = FileUpload(filename="test.txt", file="not a file object")

        with pytest.raises(
            NotImplementedError, match="does not support synchronous read"
        ):
            upload.read()

    @pytest.mark.asyncio
    async def test_aread_from_bytes(self):
        """Test aread() with bytes object"""
        upload = FileUpload(filename="test.txt", file=b"async content")

        result = await upload.aread()

        assert result == b"async content"

    @pytest.mark.asyncio
    async def test_aread_from_sync_file(self):
        """Test aread() with synchronous file-like object"""
        file_obj = io.BytesIO(b"sync file content")
        upload = FileUpload(filename="test.txt", file=file_obj)

        result = await upload.aread()

        assert result == b"sync file content"

    @pytest.mark.asyncio
    async def test_aread_from_async_file(self):
        """Test aread() with async file-like object"""
        async_file = Mock()
        async_file.read = AsyncMock(return_value=b"async file content")
        upload = FileUpload(filename="test.txt", file=async_file)

        result = await upload.aread()

        assert result == b"async file content"

    @pytest.mark.asyncio
    async def test_aread_from_async_file_returning_string(self):
        """Test aread() with async file returning string"""
        async_file = Mock()
        async_file.read = AsyncMock(return_value="async string")
        upload = FileUpload(filename="test.txt", file=async_file)

        result = await upload.aread()

        assert result == b"async string"

    @pytest.mark.asyncio
    async def test_aread_from_sync_file_returning_string(self):
        """Test aread() with sync file returning string"""
        file_obj = io.StringIO("sync string")
        upload = FileUpload(filename="test.txt", file=file_obj)

        result = await upload.aread()

        assert result == b"sync string"

    @pytest.mark.asyncio
    async def test_aread_no_read_method(self):
        """Test aread() raises error when file has no read method"""
        upload = FileUpload(filename="test.txt", file="not a file object")

        with pytest.raises(NotImplementedError, match="does not support read"):
            await upload.aread()

    def test_repr(self):
        """Test __repr__ method"""
        upload = FileUpload(filename="test.txt", content_type="text/plain", size=1024)

        result = repr(upload)

        assert (
            result
            == "FileUpload(filename='test.txt', content_type='text/plain', size=1024)"
        )

    def test_repr_minimal(self):
        """Test __repr__ with minimal params"""
        upload = FileUpload(filename="file.pdf")

        result = repr(upload)
        res = (
            "FileUpload(filename='file.pdf', "
            "content_type='application/octet-stream', size=None)"
        )
        assert result == res


class TestResponse:

    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        content = {"message": "success"}
        headers = {"X-Custom": "value"}

        response = Response(content=content, status_code=201, headers=headers)

        assert response.content == content
        assert response.status_code == 201
        assert response.headers == headers

    def test_init_with_defaults(self):
        """Test initialization with default values"""
        content = "Hello"

        response = Response(content=content)

        assert response.content == "Hello"
        assert response.status_code == 200
        assert response.headers == {}

    def test_init_with_none_headers(self):
        """Test initialization with None headers"""
        response = Response(content="test", headers=None)

        assert response.headers == {}

    def test_different_content_types(self):
        """Test Response with different content types"""
        # String content
        r1 = Response(content="text")
        assert r1.content == "text"

        # Dict content
        r2 = Response(content={"key": "value"})
        assert r2.content == {"key": "value"}

        # List content
        r3 = Response(content=[1, 2, 3])
        assert r3.content == [1, 2, 3]


class TestRequestData:

    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        file_upload = FileUpload(filename="test.txt")

        request_data = RequestData(
            path_params={"id": "123"},
            query_params={"page": "1"},
            headers={"Content-Type": "application/json"},
            cookies={"session": "abc"},
            body={"data": "test"},
            form_data={"field": "value"},
            files={"upload": file_upload},
        )

        assert request_data.path_params == {"id": "123"}
        assert request_data.query_params == {"page": "1"}
        assert request_data.headers == {"Content-Type": "application/json"}
        assert request_data.cookies == {"session": "abc"}
        assert request_data.body == {"data": "test"}
        assert request_data.form_data == {"field": "value"}
        assert request_data.files == {"upload": file_upload}

    def test_init_with_defaults(self):
        """Test initialization with default values"""
        request_data = RequestData()

        assert request_data.path_params == {}
        assert request_data.query_params == {}
        assert request_data.headers == {}
        assert request_data.cookies == {}
        assert request_data.body is None
        assert request_data.form_data == {}
        assert request_data.files == {}

    def test_init_with_none_values(self):
        """Test initialization with explicit None values"""
        request_data = RequestData(
            path_params=None,
            query_params=None,
            headers=None,
            cookies=None,
            body=None,
            form_data=None,
            files=None,
        )

        assert request_data.path_params == {}
        assert request_data.query_params == {}
        assert request_data.headers == {}
        assert request_data.cookies == {}
        assert request_data.body is None
        assert request_data.form_data == {}
        assert request_data.files == {}

    def test_files_with_list_of_uploads(self):
        """Test files parameter with list of FileUpload objects"""
        uploads = [FileUpload(filename="file1.txt"), FileUpload(filename="file2.txt")]

        request_data = RequestData(files={"images": uploads})

        assert request_data.files == {"images": uploads}

    def test_partial_initialization(self):
        """Test initialization with only some parameters"""
        request_data = RequestData(path_params={"id": "456"}, body={"message": "hello"})

        assert request_data.path_params == {"id": "456"}
        assert request_data.body == {"message": "hello"}
        assert request_data.query_params == {}
        assert request_data.headers == {}
        assert request_data.cookies == {}
        assert request_data.form_data == {}
        assert request_data.files == {}
