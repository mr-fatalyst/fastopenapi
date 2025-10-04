import json
from unittest.mock import Mock

from falcon import testing

from fastopenapi.routers.falcon.extractors import FalconRequestDataExtractor


class TestFalconRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = testing.create_req(path="/users/123/posts/test")
        request.path_params = {"id": "123", "slug": "test"}

        result = FalconRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing(self):
        """Test missing path parameters"""
        request = testing.create_req()

        result = FalconRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_with_getall(self):
        """Test query parameters with getall method"""
        request = testing.create_req(query_string="param1=value1&tags=tag1&tags=tag2")

        result = FalconRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "tags": ["tag1", "tag2"]}

    def test_get_query_params_without_getall(self):
        """Test query parameters without getall method"""
        request = testing.create_req(query_string="param1=value1&param2=value2")

        result = FalconRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_headers(self):
        """Test headers extraction"""
        request = testing.create_req(
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer token",
            }
        )

        result = FalconRequestDataExtractor._get_headers(request)

        assert "CONTENT-TYPE" in result
        assert "AUTHORIZATION" in result
        assert result["CONTENT-TYPE"] == "application/json"
        assert result["AUTHORIZATION"] == "Bearer token"

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = testing.create_req(
            headers={"Cookie": "session=abc123; csrf=token456"}
        )

        result = FalconRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    def test_get_body_json(self):
        """Test JSON body extraction"""
        body_data = {"key": "value"}
        request = testing.create_req(
            headers={"Content-Type": "application/json"}, body=json.dumps(body_data)
        )

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    def test_get_body_non_json(self):
        """Test non-JSON body"""
        request = testing.create_req(
            headers={"Content-Type": "text/plain"}, body="plain text"
        )

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_json_error(self):
        """Test JSON parsing error"""
        request = testing.create_req(
            headers={"Content-Type": "application/json"}, body='{"invalid": json}'
        )

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_empty(self):
        """Test empty JSON body"""
        request = testing.create_req(
            headers={"Content-Type": "application/json"}, body=""
        )

        result = FalconRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_form_data(self):
        """Test form data extraction"""
        request = testing.create_req(
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body="key1=value1&key2=value2",
        )

        result = FalconRequestDataExtractor._get_form_data(request)

        assert result == {"key1": "value1", "key2": "value2"}

    def test_get_files_with_files_attr(self):
        """Test files extraction with files attribute"""
        boundary = "boundary123"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="upload"; filename="test.txt"\r\n'
            f"Content-Type: text/plain\r\n\r\n"
            f"file content\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        request = testing.create_req(
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            body=body,
        )

        result = FalconRequestDataExtractor._get_files(request)

        assert isinstance(result, dict)

    def test_get_files_no_files_attr(self):
        """Test files extraction without files attribute"""
        request = testing.create_req(headers={"Content-Type": "application/json"})

        result = FalconRequestDataExtractor._get_files(request)

        assert result == {}

    def test_get_files_skip_fields_without_filename(self):
        """Test that form fields without filename are skipped"""
        mock_field = Mock()
        mock_field.secure_filename = None
        mock_field.filename = None

        mock_file = Mock()
        mock_file.secure_filename = None
        mock_file.filename = "photo.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.stream.read.return_value = b"data"
        mock_file.name = "avatar"

        request = Mock()
        request.content_type = "multipart/form-data"
        request.get_media.return_value = [mock_field, mock_file]

        result = FalconRequestDataExtractor._get_files(request)

        assert len(result) == 1
        assert "avatar" in result

    def test_get_files_multiple_files_creates_list(self):
        """Test that multiple files with same field name create a list"""
        mock_files = []
        for i in range(1, 4):
            mock_file = Mock()
            mock_file.secure_filename = None
            mock_file.filename = f"file{i}.pdf"
            mock_file.content_type = "application/pdf"
            mock_file.stream.read.return_value = f"content{i}".encode()
            mock_file.name = "docs"
            mock_files.append(mock_file)

        request = Mock()
        request.content_type = "multipart/form-data"
        request.get_media.return_value = mock_files

        result = FalconRequestDataExtractor._get_files(request)

        assert isinstance(result["docs"], list)
        assert len(result["docs"]) == 3
