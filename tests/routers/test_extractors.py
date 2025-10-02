from abc import ABC
from unittest.mock import Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.extractors import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)


class ConcreteRequestDataExtractor(BaseRequestDataExtractor):
    """Concrete implementation for testing"""

    @classmethod
    def _get_path_params(cls, request):
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request):
        return getattr(request, "query_params", {})

    @classmethod
    def _get_headers(cls, request):
        return getattr(request, "headers", {})

    @classmethod
    def _get_cookies(cls, request):
        return getattr(request, "cookies", {})

    @classmethod
    def _get_body(cls, request):
        return getattr(request, "body", {})

    @classmethod
    def _get_form_data(cls, request):
        return getattr(request, "form_data", {})

    @classmethod
    def _get_files(cls, request):
        return getattr(request, "files", {})


class ConcreteAsyncRequestDataExtractor(BaseAsyncRequestDataExtractor):
    """Concrete async implementation for testing"""

    @classmethod
    def _get_path_params(cls, request):
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request):
        return getattr(request, "query_params", {})

    @classmethod
    def _get_headers(cls, request):
        return getattr(request, "headers", {})

    @classmethod
    def _get_cookies(cls, request):
        return getattr(request, "cookies", {})

    @classmethod
    async def _get_body(cls, request):
        return getattr(request, "body", {})

    @classmethod
    async def _get_form_data(cls, request):
        return getattr(request, "form_data", {})

    @classmethod
    async def _get_files(cls, request):
        return getattr(request, "files", {})


class TestBaseRequestDataExtractor:

    def test_is_abstract(self):
        """Test that BaseRequestDataExtractor is abstract"""
        assert issubclass(BaseRequestDataExtractor, ABC)

    def test_normalize_headers(self):
        """Test header normalization"""
        headers = {"Content-Type": "application/json", "AUTHORIZATION": "Bearer token"}

        result = BaseRequestDataExtractor._normalize_headers(headers)

        assert result == {
            "content-type": "application/json",
            "authorization": "Bearer token",
        }

    def test_normalize_headers_empty(self):
        """Test normalizing empty headers"""
        result = BaseRequestDataExtractor._normalize_headers({})

        assert result == {}

    def test_normalize_headers_none(self):
        """Test normalizing None headers"""
        result = BaseRequestDataExtractor._normalize_headers(None)

        assert result == {}

    def test_safe_json_parse_valid_string(self):
        """Test parsing valid JSON string"""
        data = '{"key": "value"}'

        result = BaseRequestDataExtractor._safe_json_parse(data)

        assert result == {"key": "value"}

    def test_safe_json_parse_valid_bytes(self):
        """Test parsing valid JSON bytes"""
        data = b'{"key": "value"}'

        result = BaseRequestDataExtractor._safe_json_parse(data)

        assert result == {"key": "value"}

    def test_safe_json_parse_valid_bytearray(self):
        """Test parsing valid JSON bytearray"""
        data = bytearray(b'{"key": "value"}')

        result = BaseRequestDataExtractor._safe_json_parse(data)

        assert result == {"key": "value"}

    def test_safe_json_parse_already_dict(self):
        """Test parsing data that's already a dict"""
        data = {"key": "value"}

        result = BaseRequestDataExtractor._safe_json_parse(data)

        assert result == {"key": "value"}

    def test_safe_json_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        data = '{"invalid": json}'

        result = BaseRequestDataExtractor._safe_json_parse(data)

        assert result is None

    def test_safe_json_parse_empty_string(self):
        """Test parsing empty string"""
        result = BaseRequestDataExtractor._safe_json_parse("")

        assert result is None

    def test_safe_json_parse_none(self):
        """Test parsing None"""
        result = BaseRequestDataExtractor._safe_json_parse(None)

        assert result is None

    def test_safe_json_parse_unicode_decode_error(self):
        """Test parsing bytes with invalid encoding"""
        data = b"\xff\xfe"  # Invalid UTF-8

        result = BaseRequestDataExtractor._safe_json_parse(data)

        assert result is None

    def test_extract_request_data_with_path_params(self):
        """Test extracting request data with provided path params"""
        request = Mock()
        request.query_params = {"param": "value"}
        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.body = {"data": "test"}
        request.form_data = {"field": "form_value"}
        request.files = {"upload": b"file_content"}

        env = RequestEnvelope(request=request, path_params={"id": "123"})

        result = ConcreteRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"field": "form_value"}
        assert result.files == {"upload": b"file_content"}

    def test_extract_request_data_without_path_params(self):
        """Test extracting request data without provided path params"""
        request = Mock()
        request.path_params = {"extracted": "param"}
        request.query_params = {"param": "value"}
        request.headers = {"Authorization": "Bearer token"}
        request.cookies = {}
        request.body = {}
        request.form_data = {}
        request.files = {}

        env = RequestEnvelope(request=request, path_params=None)

        result = ConcreteRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"extracted": "param"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"authorization": "Bearer token"}
        assert result.cookies == {}
        assert result.body == {}
        assert result.form_data == {}
        assert result.files == {}


class TestBaseAsyncRequestDataExtractor:

    def test_inherits_from_base(self):
        """Test that async extractor inherits from base"""
        assert issubclass(BaseAsyncRequestDataExtractor, BaseRequestDataExtractor)

    def test_is_abstract(self):
        """Test that BaseAsyncRequestDataExtractor is abstract"""
        assert issubclass(BaseAsyncRequestDataExtractor, ABC)

    @pytest.mark.asyncio
    async def test_extract_request_data_async_with_path_params(self):
        """Test async extracting request data with provided path params"""
        request = Mock()
        request.query_params = {"param": "value"}
        request.headers = {"Content-Type": "application/json"}
        request.cookies = {"session": "abc"}
        request.body = {"data": "test"}
        request.form_data = {"field": "form_value"}
        request.files = {"upload": b"file_content"}

        env = RequestEnvelope(request=request, path_params={"id": "123"})

        result = await ConcreteAsyncRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"field": "form_value"}
        assert result.files == {"upload": b"file_content"}

    @pytest.mark.asyncio
    async def test_extract_request_data_async_without_path_params(self):
        """Test async extracting request data without provided path params"""
        request = Mock()
        request.path_params = {"extracted": "param"}
        request.query_params = {"param": "value"}
        request.headers = {"Authorization": "Bearer token"}
        request.cookies = {}
        request.body = {}
        request.form_data = {}
        request.files = {}

        env = RequestEnvelope(request=request, path_params=None)

        result = await ConcreteAsyncRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"extracted": "param"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"authorization": "Bearer token"}
        assert result.cookies == {}
        assert result.body == {}
        assert result.form_data == {}
        assert result.files == {}


class TestAbstractMethods:
    """Test that abstract methods raise NotImplementedError when not overridden"""

    def test_base_abstract_methods_not_implemented(self):
        """Test that base abstract methods are not implemented"""
        with pytest.raises(TypeError):
            BaseRequestDataExtractor()

    def test_async_abstract_methods_not_implemented(self):
        """Test that async abstract methods are not implemented"""
        with pytest.raises(TypeError):
            BaseAsyncRequestDataExtractor()
