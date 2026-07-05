import inspect
from abc import ABC, abstractmethod
from typing import Any

from pydantic_core import from_json

from fastopenapi.core.constants import NO_BODY_METHODS
from fastopenapi.core.types import FileUpload, RequestData
from fastopenapi.errors.exceptions import ValidationError
from fastopenapi.resolution.profile import EXTRACT_ALL, ExtractionProfile
from fastopenapi.routers.common import RequestEnvelope


class BaseRequestDataExtractor(ABC):
    """Base request data extractor with common logic extraction"""

    @classmethod
    @abstractmethod
    def _get_path_params(cls, request: Any) -> dict[str, Any]:
        """Extract path parameters"""

    @classmethod
    @abstractmethod
    def _get_query_params(cls, request: Any) -> dict[str, Any]:
        """Extract query parameters"""

    @classmethod
    @abstractmethod
    def _get_headers(cls, request: Any) -> dict[str, Any]:
        """Extract headers"""

    @classmethod
    @abstractmethod
    def _get_cookies(cls, request: Any) -> dict[str, Any]:
        """Extract cookies"""

    @classmethod
    @abstractmethod
    def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""

    @classmethod
    @abstractmethod
    def _get_form_data(cls, request: Any) -> dict[str, Any]:
        """Extract form data"""

    @classmethod
    @abstractmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""

    @staticmethod
    def _normalize_headers(headers: dict[str, Any]) -> dict[str, Any]:
        """Normalize headers to lowercase"""
        return {k.lower(): v for k, v in headers.items()} if headers else {}

    @staticmethod
    def _is_json_content(content_type: Any) -> bool:
        """Check if the declared Content-Type is a JSON media type"""
        mimetype = str(content_type or "").partition(";")[0].strip().lower()
        return mimetype == "application/json" or mimetype.endswith("+json")

    @staticmethod
    def _safe_json_parse(
        data: Any, strict: bool = False
    ) -> dict[str, Any] | list[Any] | None:
        """Parse JSON data.

        With strict=True (the request declared a JSON Content-Type) a
        malformed payload raises ValidationError instead of being dropped,
        so the client gets a JSON parse error rather than 'Field required'.
        """
        if not data:
            return None
        try:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")
            if isinstance(data, str):
                return from_json(data)
            return data
        except Exception as e:
            if strict:
                raise ValidationError(
                    "Invalid JSON in request body", details=str(e)
                ) from e
            return None

    @classmethod
    def extract_request_data(
        cls, env: RequestEnvelope, profile: ExtractionProfile | None = None
    ) -> RequestData:
        """Synchronous request data extraction.

        Stream-consuming payloads (body/form/files) are read only when the
        endpoint's extraction profile references them.
        """
        profile = profile or EXTRACT_ALL
        _path_params = env.path_params
        request = env.request
        if _path_params is None:
            _path_params = cls._get_path_params(request)
        has_payload = request.method not in NO_BODY_METHODS
        return RequestData(
            path_params=_path_params,
            query_params=cls._get_query_params(request),
            headers=cls._normalize_headers(cls._get_headers(request)),
            cookies=cls._get_cookies(request),
            body=(cls._get_body(request) if has_payload and profile.needs_body else {}),
            form_data=(
                cls._get_form_data(request)
                if has_payload and profile.needs_form
                else {}
            ),
            files=(
                cls._get_files(request) if has_payload and profile.needs_files else {}
            ),
        )


class BaseAsyncRequestDataExtractor(BaseRequestDataExtractor, ABC):
    """Base async request data extractor with common logic extraction"""

    _REQUIRED_ASYNC = ("_get_body", "_get_form_data", "_get_files")

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Refuse subclasses that inherit synchronous payload readers.

        Guards against the Falcon-ASGI class of bugs: an async extractor
        silently inheriting WSGI code fails at import time, not per request.
        """
        super().__init_subclass__(**kwargs)
        for name in cls._REQUIRED_ASYNC:
            attr = inspect.getattr_static(cls, name, None)
            if attr is None:
                continue
            func = (
                attr.__func__ if isinstance(attr, (classmethod, staticmethod)) else attr
            )
            if getattr(func, "__isabstractmethod__", False):
                continue
            if not inspect.iscoroutinefunction(func):
                raise TypeError(
                    f"{cls.__name__}.{name} must be 'async def': async "
                    f"extractors must not inherit synchronous payload readers"
                )

    @classmethod
    @abstractmethod
    async def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""

    @classmethod
    @abstractmethod
    async def _get_form_data(cls, request: Any) -> dict[str, Any]:
        """Extract form data"""

    @classmethod
    @abstractmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""

    @classmethod
    async def extract_request_data(
        cls, env: RequestEnvelope, profile: ExtractionProfile | None = None
    ) -> RequestData:
        """Asynchronous request data extraction.

        Stream-consuming payloads (body/form/files) are read only when the
        endpoint's extraction profile references them.
        """
        profile = profile or EXTRACT_ALL
        _path_params = env.path_params
        request = env.request
        if _path_params is None:
            _path_params = cls._get_path_params(request)
        has_payload = request.method not in NO_BODY_METHODS
        return RequestData(
            path_params=_path_params,
            query_params=cls._get_query_params(request),
            headers=cls._normalize_headers(cls._get_headers(request)),
            cookies=cls._get_cookies(request),
            body=(
                await cls._get_body(request)
                if has_payload and profile.needs_body
                else {}
            ),
            form_data=(
                await cls._get_form_data(request)
                if has_payload and profile.needs_form
                else {}
            ),
            files=(
                await cls._get_files(request)
                if has_payload and profile.needs_files
                else {}
            ),
        )
