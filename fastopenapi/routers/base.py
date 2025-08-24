import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic_core import from_json

from fastopenapi.core.router import BaseRouter
from fastopenapi.core.types import RequestData, Response
from fastopenapi.errors.exceptions import APIError
from fastopenapi.resolution.resolver import ParameterResolver
from fastopenapi.response.builder import ResponseBuilder


@dataclass(slots=True, frozen=True)
class RequestEnvelope:
    """Unified wrapper for requests."""

    path_params: dict[str, str]
    request: Any | None


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
    def _get_files(cls, request: Any) -> dict:
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
            body=cls._get_body(request),
            form_data=cls._get_form_data(request),
            files=cls._get_files(request),
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
    async def _get_files(cls, request: Any) -> dict:
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
            body=await cls._get_body(request),
            form_data=await cls._get_form_data(request),
            files=await cls._get_files(request),
        )


class BaseAdapter(BaseRouter, ABC):
    """Base adapter for framework integration"""

    # Path conversion pattern
    PATH_CONVERSIONS = (r"{(\w+)}", r"{\1}")
    EXCEPTION_MAPPER = {}

    extractor_cls = BaseRequestDataExtractor
    extractor_async_cls = BaseAsyncRequestDataExtractor
    req_param_resolver_cls = ParameterResolver
    response_builder_cls = ResponseBuilder

    @abstractmethod
    def build_framework_response(self, response: Response) -> Any:
        """Build framework-specific response object"""

    @classmethod
    def _convert_path_for_framework(cls, path: str) -> str:
        """Convert path format for specific framework"""
        pattern, replacement = cls.PATH_CONVERSIONS
        return re.sub(pattern, replacement, path)

    def handle_request(self, endpoint: Callable, env: RequestEnvelope) -> Any:
        """Handle synchronous request"""
        try:
            request_data = self.extractor_cls.extract_request_data(env)
            kwargs = self.req_param_resolver_cls.resolve(endpoint, request_data)
            result = endpoint(**kwargs)
            response = self.response_builder_cls.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)
        except Exception as e:
            api_error = APIError.from_exception(e, self.EXCEPTION_MAPPER)
            return self.build_framework_response(
                Response(
                    content=api_error.to_response(),
                    status_code=api_error.status_code,
                )
            )

    async def handle_request_async(
        self, endpoint: Callable, env: RequestEnvelope
    ) -> Any:
        """Handle asynchronous request"""
        try:
            request_data = await self.extractor_async_cls.extract_request_data(env)
            kwargs = self.req_param_resolver_cls.resolve(endpoint, request_data)
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)
            response = self.response_builder_cls.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)
        except Exception as e:
            api_error = APIError.from_exception(e, self.EXCEPTION_MAPPER)
            return self.build_framework_response(
                Response(
                    content=api_error.to_response(),
                    status_code=api_error.status_code,
                )
            )
