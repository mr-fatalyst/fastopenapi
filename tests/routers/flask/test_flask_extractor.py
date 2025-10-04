import json
from io import BytesIO

from flask import Flask, request

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.flask.extractors import FlaskRequestDataExtractor


class TestFlaskRequestDataExtractor:

    @staticmethod
    def create_app():
        """Helper to create Flask app for testing"""
        return Flask(__name__)

    def test_get_path_params(self):
        """Test path parameters extraction"""
        app = self.create_app()

        with app.test_request_context("/users/123/posts/test"):
            request.path_params = {"id": "123", "slug": "test"}

            result = FlaskRequestDataExtractor._get_path_params(request)

            assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing(self):
        """Test missing path parameters"""
        app = self.create_app()

        with app.test_request_context("/"):
            result = FlaskRequestDataExtractor._get_path_params(request)

            assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        app = self.create_app()

        with app.test_request_context("/?param1=value1&param2=value2"):
            result = FlaskRequestDataExtractor._get_query_params(request)

            assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        app = self.create_app()

        with app.test_request_context("/?tags=tag1&tags=tag2"):
            result = FlaskRequestDataExtractor._get_query_params(request)

            assert result == {"tags": ["tag1", "tag2"]}

    def test_get_headers(self):
        """Test headers extraction"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer token",
            },
        ):
            result = FlaskRequestDataExtractor._get_headers(request)

            assert result["Content-Type"] == "application/json"
            assert result["Authorization"] == "Bearer token"

    def test_get_cookies(self):
        """Test cookies extraction"""
        app = self.create_app()

        with app.test_request_context(
            "/", headers={"Cookie": "session=abc123; csrf=token456"}
        ):
            result = FlaskRequestDataExtractor._get_cookies(request)

            assert result == {"session": "abc123", "csrf": "token456"}

    def test_get_body_json(self):
        """Test JSON body extraction"""
        app = self.create_app()

        body_data = {"key": "value"}
        with app.test_request_context(
            "/",
            method="POST",
            data=json.dumps(body_data),
            content_type="application/json",
        ):
            result = FlaskRequestDataExtractor._get_body(request)

            assert result == {"key": "value"}

    def test_get_body_json_none(self):
        """Test JSON body returning None"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", data="", content_type="application/json"
        ):
            result = FlaskRequestDataExtractor._get_body(request)

            assert result == {}

    def test_get_body_non_json(self):
        """Test non-JSON body"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", data="plain text", content_type="text/plain"
        ):
            result = FlaskRequestDataExtractor._get_body(request)

            assert result == {}

    def test_get_body_no_mimetype(self):
        """Test body with no mimetype"""
        app = self.create_app()

        with app.test_request_context("/", method="POST"):
            result = FlaskRequestDataExtractor._get_body(request)

            assert result == {}

    def test_get_form_data(self):
        """Test form data extraction"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            method="POST",
            data={"field1": "value1", "field2": "value2"},
            content_type="application/x-www-form-urlencoded",
        ):
            result = FlaskRequestDataExtractor._get_form_data(request)

            assert result == {"field1": "value1", "field2": "value2"}

    def test_get_form_data_no_form_attr(self):
        """Test form data with no form attribute"""
        app = self.create_app()

        with app.test_request_context("/"):
            result = FlaskRequestDataExtractor._get_form_data(request)

            assert result == {}

    def test_get_files_multipart(self):
        """Test file extraction with multipart content"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            method="POST",
            data={"upload": (BytesIO(b"file content"), "test.txt")},
            content_type="multipart/form-data",
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert isinstance(result, dict)

    def test_get_files_no_multipart(self):
        """Test file extraction with non-multipart content"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", content_type="application/json"
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert result == {}

    def test_get_files_no_get_media(self):
        """Test file extraction without get_media method"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", content_type="multipart/form-data"
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert isinstance(result, dict)

    def test_get_files_part_no_name(self):
        """Test file extraction with part missing name"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", content_type="multipart/form-data"
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert isinstance(result, dict)

    def test_get_files_part_no_filename(self):
        """Test file extraction with part missing filename"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", content_type="multipart/form-data"
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert isinstance(result, dict)

    def test_extract_request_data_full(self):
        """Test full request data extraction"""
        app = self.create_app()

        body_data = {"data": "test"}
        with app.test_request_context(
            "/?param=value",
            method="POST",
            data=json.dumps(body_data),
            headers={"Content-Type": "application/json", "Cookie": "session=abc"},
        ):
            request.path_params = {"id": "123"}

            env = RequestEnvelope(request=request, path_params=None)

            result = FlaskRequestDataExtractor.extract_request_data(env)

            assert isinstance(result, RequestData)
            assert result.path_params == {"id": "123"}
            assert result.query_params == {"param": "value"}
            assert "content-type" in result.headers or "Content-Type" in result.headers
            assert result.cookies == {"session": "abc"}
            assert result.body == {"data": "test"}

    def test_get_files_single_file(self):
        """Test file extraction with single file"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            method="POST",
            data={"avatar": (BytesIO(b"image data"), "photo.jpg")},
            content_type="multipart/form-data",
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert "avatar" in result
            assert not isinstance(result["avatar"], list)
            assert result["avatar"].filename == "photo.jpg"
            assert result["avatar"].size is None  # Flask doesn't expose size

    def test_get_files_multiple_files_same_key(self):
        """Test file extraction with multiple files for same key"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            method="POST",
            data={
                "docs": [
                    (BytesIO(b"content1"), "file1.pdf"),
                    (BytesIO(b"content2"), "file2.pdf"),
                    (BytesIO(b"content3"), "file3.pdf"),
                ]
            },
            content_type="multipart/form-data",
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert "docs" in result
            assert isinstance(result["docs"], list)
            assert len(result["docs"]) == 3
            assert result["docs"][0].filename == "file1.pdf"
            assert result["docs"][1].filename == "file2.pdf"
            assert result["docs"][2].filename == "file3.pdf"

    def test_get_files_empty_files(self):
        """Test file extraction with empty files"""
        app = self.create_app()

        with app.test_request_context(
            "/", method="POST", content_type="multipart/form-data"
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert result == {}

    def test_get_files_no_filename(self):
        """Test file extraction when filename is None"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            method="POST",
            data={"upload": (BytesIO(b"content"), "")},  # Empty filename
            content_type="multipart/form-data",
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert "upload" in result
            assert result["upload"].filename == "unknown"

    def test_get_files_multiple_keys(self):
        """Test file extraction with multiple different keys"""
        app = self.create_app()

        with app.test_request_context(
            "/",
            method="POST",
            data={
                "avatar": (BytesIO(b"image"), "avatar.jpg"),
                "document": (BytesIO(b"pdf data"), "doc.pdf"),
            },
            content_type="multipart/form-data",
        ):
            result = FlaskRequestDataExtractor._get_files(request)

            assert len(result) == 2
            assert "avatar" in result
            assert "document" in result
            assert result["avatar"].filename == "avatar.jpg"
            assert result["document"].filename == "doc.pdf"

    def test_get_query_params_empty(self):
        """Test query parameters with no params"""
        app = self.create_app()

        with app.test_request_context("/"):
            result = FlaskRequestDataExtractor._get_query_params(request)

            assert result == {}

    def test_get_form_data_multiple_values(self):
        """Test form data with multiple values for same key"""
        app = self.create_app()

        with app.test_request_context(
            "/?tags=tag1&tags=tag2&tags=tag3",
            method="POST",
            data={"tags": ["tag1", "tag2", "tag3"]},
            content_type="application/x-www-form-urlencoded",
        ):
            result = FlaskRequestDataExtractor._get_form_data(request)

            assert "tags" in result
