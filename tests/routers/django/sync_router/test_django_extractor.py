from unittest.mock import Mock

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoRequestDataExtractor


class TestDjangoRequestDataExtractor:

    def test_get_path_params(self):
        """Test path parameters extraction"""
        request = Mock()
        request.path_params = {"id": "123", "slug": "test"}

        result = DjangoRequestDataExtractor._get_path_params(request)

        assert result == {"id": "123", "slug": "test"}

    def test_get_path_params_missing_attr(self):
        """Test path parameters when attribute missing"""
        request = Mock(spec=[])  # No path_params attribute

        result = DjangoRequestDataExtractor._get_path_params(request)

        assert result == {}

    def test_get_query_params_single_values(self):
        """Test query parameters with single values"""
        request = Mock()
        request.GET = Mock()
        request.GET.keys = Mock(return_value=["param1", "param2"])
        request.GET.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "param1" else ["value2"]
        )

        result = DjangoRequestDataExtractor._get_query_params(request)

        assert result == {"param1": "value1", "param2": "value2"}

    def test_get_query_params_multiple_values(self):
        """Test query parameters with multiple values"""
        request = Mock()
        request.GET = Mock()
        request.GET.keys = Mock(return_value=["tags"])
        request.GET.getlist = Mock(return_value=["tag1", "tag2"])

        result = DjangoRequestDataExtractor._get_query_params(request)

        assert result == {"tags": ["tag1", "tag2"]}

    def test_get_headers(self):
        """Test headers extraction"""
        request = Mock()
        request.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

        result = DjangoRequestDataExtractor._get_headers(request)

        assert result == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }

    def test_get_cookies(self):
        """Test cookies extraction"""
        request = Mock()
        request.COOKIES = {"session": "abc123", "csrf": "token456"}

        result = DjangoRequestDataExtractor._get_cookies(request)

        assert result == {"session": "abc123", "csrf": "token456"}

    def test_get_body_json(self):
        """Test JSON body extraction"""
        request = Mock()
        request.body = b'{"key": "value"}'

        result = DjangoRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    def test_get_body_empty(self):
        """Test empty body"""
        request = Mock()
        request.body = b""

        result = DjangoRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_no_body_attr(self):
        """Test missing body attribute"""
        request = Mock(spec=[])  # No body attribute

        result = DjangoRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_body_invalid_json(self):
        """Test invalid JSON body"""
        request = Mock()
        request.body = b'{"invalid": json}'

        result = DjangoRequestDataExtractor._get_body(request)

        assert result == {}

    def test_get_form_data(self):
        """Test form data extraction"""
        request = Mock()
        request.POST = Mock()
        request.POST.keys = Mock(return_value=["field1", "field2"])
        request.POST.getlist = Mock(
            side_effect=lambda k: ["value1"] if k == "field1" else ["value2"]
        )

        result = DjangoRequestDataExtractor._get_form_data(request)

        assert result == {"field1": "value1", "field2": "value2"}

    def test_get_form_data_no_post_attr(self):
        """Test missing POST attribute"""
        request = Mock(spec=[])  # No POST attribute

        result = DjangoRequestDataExtractor._get_form_data(request)

        assert result == {}

    def test_get_files(self):
        """Test files extraction"""
        request = Mock()

        result = DjangoRequestDataExtractor._get_files(request)

        assert result == {}

    def test_extract_request_data_full(self):
        """Test full request data extraction"""
        request = Mock()
        request.path_params = {"id": "123"}
        request.GET = Mock()
        request.GET.keys = Mock(return_value=["param"])
        request.GET.getlist = Mock(return_value=["value"])
        request.headers = {"Content-Type": "application/json"}
        request.COOKIES = {"session": "abc"}
        request.body = b'{"data": "test"}'
        request.POST = Mock()
        request.POST.keys = Mock(return_value=["form_field"])
        request.POST.getlist = Mock(return_value=["form_value"])

        env = RequestEnvelope(request=request, path_params=None)

        result = DjangoRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
