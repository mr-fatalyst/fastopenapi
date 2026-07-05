from abc import ABC
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import ValidationError
from fastopenapi.resolution.profile import ExtractionProfile
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

    def test_safe_json_parse_strict_invalid_json_raises(self):
        """Strict mode turns malformed JSON into a 422 ValidationError"""
        with pytest.raises(ValidationError):
            BaseRequestDataExtractor._safe_json_parse('{"invalid": json}', strict=True)

    def test_safe_json_parse_strict_empty_returns_none(self):
        """Strict mode still treats an empty body as absent, not malformed"""
        result = BaseRequestDataExtractor._safe_json_parse(b"", strict=True)

        assert result is None

    def test_is_json_content(self):
        """JSON media types are detected with parameters and suffixes"""
        assert BaseRequestDataExtractor._is_json_content("application/json")
        assert BaseRequestDataExtractor._is_json_content(
            "application/json; charset=utf-8"
        )
        assert BaseRequestDataExtractor._is_json_content("application/problem+json")
        assert not BaseRequestDataExtractor._is_json_content("text/plain")
        assert not BaseRequestDataExtractor._is_json_content(None)
        assert not BaseRequestDataExtractor._is_json_content("")


class TestAsyncExtractorGuard:
    """__init_subclass__ must refuse async extractors with sync payload readers"""

    def test_sync_get_body_rejected(self):
        with pytest.raises(TypeError, match="_get_body"):

            class BadBody(ConcreteAsyncRequestDataExtractor):
                @classmethod
                def _get_body(cls, request):
                    return {}

    def test_sync_form_reader_rejected(self):
        with pytest.raises(TypeError, match="_get_form_data"):

            class BadForm(ConcreteAsyncRequestDataExtractor):
                @classmethod
                def _get_form_data(cls, request):
                    return {}

    def test_sync_files_reader_rejected(self):
        with pytest.raises(TypeError, match="_get_files"):

            class BadFiles(ConcreteAsyncRequestDataExtractor):
                @classmethod
                def _get_files(cls, request):
                    return {}

    def test_inherited_sync_readers_rejected(self):
        """The Falcon-ASGI trap: async extractor inheriting sync readers"""
        with pytest.raises(TypeError, match="must be 'async def'"):

            class Trap(ConcreteRequestDataExtractor, BaseAsyncRequestDataExtractor):
                pass

    def test_proper_async_subclass_accepted(self):
        class Fine(ConcreteAsyncRequestDataExtractor):
            @classmethod
            async def _get_body(cls, request):
                return {"ok": True}

        assert Fine is not None


class TestExtractionProfileGating:
    """Payload readers run only when the profile references them"""

    @staticmethod
    def _probe(calls):
        class Probe(ConcreteRequestDataExtractor):
            @classmethod
            def _get_body(cls, request):
                calls.append("body")
                return {}

            @classmethod
            def _get_form_data(cls, request):
                calls.append("form")
                return {}

            @classmethod
            def _get_files(cls, request):
                calls.append("files")
                return {}

        return Probe

    def test_profile_gates_payload_extraction(self):
        calls = []
        probe = self._probe(calls)
        request = SimpleNamespace(method="POST")
        env = RequestEnvelope(request=request, path_params={})
        profile = ExtractionProfile(
            needs_body=False, needs_form=True, needs_files=False
        )

        probe.extract_request_data(env, profile)

        assert calls == ["form"]

    def test_no_profile_extracts_everything(self):
        calls = []
        probe = self._probe(calls)
        request = SimpleNamespace(method="POST")
        env = RequestEnvelope(request=request, path_params={})

        probe.extract_request_data(env)

        assert calls == ["body", "form", "files"]

    def test_no_body_methods_skip_payloads_regardless_of_profile(self):
        calls = []
        probe = self._probe(calls)
        request = SimpleNamespace(method="GET")
        env = RequestEnvelope(request=request, path_params={})

        probe.extract_request_data(env, ExtractionProfile(True, True, True))

        assert calls == []

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


class TestAsyncExtractorGuardEdges:
    def test_abstract_async_override_accepted(self):
        """Re-declared abstract readers are skipped by the guard"""
        from abc import abstractmethod

        class StillAbstract(BaseAsyncRequestDataExtractor):
            @classmethod
            @abstractmethod
            async def _get_body(cls, request):
                """Still abstract"""

        assert StillAbstract is not None
