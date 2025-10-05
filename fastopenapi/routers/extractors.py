from abc import ABC, abstractmethod
from typing import Any

from pydantic_core import from_json

from fastopenapi.core.constants import NO_BODY_METHODS
from fastopenapi.core.types import FileUpload, RequestData
from fastopenapi.routers.common import RequestEnvelope


class BaseRequestDataExtractor(ABC):
    """Base request data extractor with common logic extraction"""

    @classmethod
    @abstractmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""

    @classmethod
    @abstractmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""

    @classmethod
    @abstractmethod
    def _get_headers(cls, request: Any) -> dict:
        """Extract headers"""

    @classmethod
    @abstractmethod
    def _get_cookies(cls, request: Any) -> dict:
        """Extract cookies"""

    @classmethod
    @abstractmethod
    def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""

    @classmethod
    @abstractmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""

    @classmethod
    @abstractmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""

    @staticmethod
    def _normalize_headers(headers: dict) -> dict:
        """Normalize headers to lowercase"""
        return {k.lower(): v for k, v in headers.items()} if headers else {}

    @staticmethod
    def _safe_json_parse(data: Any) -> dict | None:
        """Safely parse JSON data"""
        if not data:
            return None
        try:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")
            if isinstance(data, str):
                return from_json(data)
            return data
        except Exception:
            return None

    @classmethod
    def extract_request_data(cls, env: RequestEnvelope) -> RequestData:
        """Synchronous request data extraction"""
        _path_params = env.path_params
        request = env.request
        if _path_params is None:
            _path_params = cls._get_path_params(request)
        return RequestData(
            path_params=_path_params,
            query_params=cls._get_query_params(request),
            headers=cls._normalize_headers(cls._get_headers(request)),
            cookies=cls._get_cookies(request),
            body=(
                cls._get_body(request) if request.method not in NO_BODY_METHODS else {}
            ),
            form_data=(
                cls._get_form_data(request)
                if request.method not in NO_BODY_METHODS
                else {}
            ),
            files=(
                cls._get_files(request) if request.method not in NO_BODY_METHODS else {}
            ),
        )


class BaseAsyncRequestDataExtractor(BaseRequestDataExtractor, ABC):
    """Base async request data extractor with common logic extraction"""

    @classmethod
    @abstractmethod
    async def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""

    @classmethod
    @abstractmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""

    @classmethod
    @abstractmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""

    @classmethod
    async def extract_request_data(cls, env: RequestEnvelope) -> RequestData:
        """Asynchronous request data extraction"""
        _path_params = env.path_params
        request = env.request
        if _path_params is None:
            _path_params = cls._get_path_params(request)
        return RequestData(
            path_params=_path_params,
            query_params=cls._get_query_params(request),
            headers=cls._normalize_headers(cls._get_headers(request)),
            cookies=cls._get_cookies(request),
            body=(
                await cls._get_body(request)
                if request.method not in NO_BODY_METHODS
                else {}
            ),
            form_data=(
                await cls._get_form_data(request)
                if request.method not in NO_BODY_METHODS
                else {}
            ),
            files=(
                await cls._get_files(request)
                if request.method not in NO_BODY_METHODS
                else {}
            ),
        )
