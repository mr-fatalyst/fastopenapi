import io
from unittest.mock import Mock

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.flask.extractors import FlaskRequestDataExtractor


class TestFlaskRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_params = {"id": "123", "slug": "test"}

        result = FlaskRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing(self):
        """Test missing path parameters"""
        request = Mock(spec=[])

        result = FlaskRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        request.args = Mock()
        request.args.__iter__ = Mock(return_value=iter(["param1", "param2"]))
        request.args.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["value2"]
        )

        result = FlaskRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        request.args = Mock()
        request.args.__iter__ = Mock(return_value=iter(["tags"]))
        request.args.getlist = Mock(return_value=["tag1", "tag2"])

        result = FlaskRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2"]}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = FlaskRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.cookies = {"session": "abc123", "csrf": "token456"}

        result = FlaskRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.mimetype = "application/json"
        request.get_json = Mock(return_value={"key": "value"})

        result = FlaskRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}
        request.get_json.assert_called_once_with(silent=True)

    def test_get_body_json_none(self):
        """Test JSON body returning None"""
        request = Mock()
        request.mimetype = "application/json"
        request.get_json = Mock(return_value=None)

        result = FlaskRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_non_json(self):
        """Test non-JSON body"""
        request = Mock()
        request.mimetype = "text/plain"

        result = FlaskRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_no_mimetype(self):
        """Test body with no mimetype"""
        request = Mock()
        request.mimetype = None

        result = FlaskRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_form_data(self):
        """Test form data extraction"""
        request = Mock()
        request.form = {"field1": "value1", "field2": "value2"}

        result = FlaskRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    def test_get_form_data_no_form_attr(self):
        """Test form data with no form attribute"""
        request = Mock(spec=[])

        result = FlaskRequestDataExtractor._get_form_data(request)

        assert result == {}

    def test_get_files_multipart(self):
        """Test file extraction with multipart content"""
        request = Mock()
        request.content_type = "multipart/form-data; boundary=something"

        # Mock get_media method
        part_mock = Mock()
        part_mock.name = "upload"
        part_mock.secure_filename = "test.txt"
        part_mock.stream = io.BytesIO(b"file content")

        request.get_media = Mock(return_value=[part_mock])

        result = FlaskRequestDataExtractor._get_files(request)

        assert result == {"upload": b"file content"}

    def test_get_files_no_multipart(self):
        """Test file extraction with non-multipart content"""
        request = Mock()
        request.content_type = "application/json"

        result = FlaskRequestDataExtractor._get_files(request)

        assert result == {}

    def test_get_files_no_get_media(self):
        """Test file extraction without get_media method"""
        request = Mock(spec=["content_type"])
        request.content_type = "multipart/form-data"

        result = FlaskRequestDataExtractor._get_files(request)

        assert result == {}

    def test_get_files_part_no_name(self):
        """Test file extraction with part missing name"""
        request = Mock()
        request.content_type = "multipart/form-data"

        part_mock = Mock()
        part_mock.name = None
        part_mock.secure_filename = "test.txt"

        request.get_media = Mock(return_value=[part_mock])

        result = FlaskRequestDataExtractor._get_files(request)

        assert result == {}

    def test_get_files_part_no_filename(self):
        """Test file extraction with part missing filename"""
        request = Mock()
        request.content_type = "multipart/form-data"

        part_mock = Mock()
        part_mock.name = "upload"
        part_mock.secure_filename = None
        part_mock.filename = None

        request.get_media = Mock(return_value=[part_mock])

        result = FlaskRequestDataExtractor._get_files(request)

        assert result == {}

    def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.path_params = {"id": "123"}
        request.args = Mock()
        request.args.__iter__ = Mock(return_value=iter(["param"]))
        request.args.getlist = Mock(return_value=["value"])
        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.mimetype = "application/json"
        request.get_json = Mock(return_value={"data": "test"})
        request.form = {"form_field": "form_value"}
        request.content_type = "application/json"

        env = RequestEnvelope(request=request, path_params=None)

        result = FlaskRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
