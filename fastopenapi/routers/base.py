import inspect
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from fastopenapi.core.router import BaseRouter
from fastopenapi.core.types import RequestData, Response
from fastopenapi.errors.exceptions import APIError
from fastopenapi.resolution.resolver import ParameterResolver
from fastopenapi.response.builder import ResponseBuilder


class BaseAdapter(BaseRouter, ABC):
    """Base adapter for framework integration with common logic extraction"""

    # Path conversion patterns
    PATH_CONVERSIONS = {
        "flask": (r"{(\w+)}", r"<\1>"),
        "django": (r"{(\w+)}", r"<\1>"),
        "sanic": (r"{(\w+)}", r"<\1>"),
        "tornado": (r"{(\w+)}", r"(?P<\1>[^/]+)"),
        "default": (r"{(\w+)}", r"{\1}"),
    }

    EXCEPTION_MAPPER = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resolver = ParameterResolver()
        self.response_builder = ResponseBuilder()

    def handle_request_sync(self, endpoint: Callable, request: Any) -> Any:
        """Handle synchronous request"""
        try:
            request_data = self.extract_request_data(request)
            kwargs = self.resolver.resolve(endpoint, request_data)
            result = endpoint(**kwargs)
            response = self.response_builder.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)
        except Exception as e:
            api_error = APIError.from_exception(e, self.EXCEPTION_MAPPER)
            return self.build_framework_response(
                Response(
                    content=api_error.to_response(),
                    status_code=api_error.status_code,
                )
            )

    async def handle_request_async(self, endpoint: Callable, request: Any) -> Any:
        """Handle asynchronous request"""
        try:
            request_data = await self.extract_request_data_async(request)
            kwargs = self.resolver.resolve(endpoint, request_data)
            result = await endpoint(**kwargs)
            response = self.response_builder.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)
        except Exception as e:
            api_error = APIError.from_exception(e, self.EXCEPTION_MAPPER)
            return self.build_framework_response(
                Response(
                    content=api_error.to_response(),
                    status_code=api_error.status_code,
                )
            )

    def extract_request_data(self, request: Any) -> RequestData:
        """Synchronous request data extraction"""
        return RequestData(
            path_params=self._get_path_params(request),
            query_params=self._get_query_params(request),
            headers=self._normalize_headers(self._get_headers(request)),
            cookies=self._get_cookies(request),
            body=self._safe_json_parse(self._get_body_sync(request)),
            form_data=self._get_form_data_sync(request),
            files=self._get_files_sync(request),
        )

    async def extract_request_data_async(self, request: Any) -> RequestData:
        """Asynchronous request data extraction"""
        body = await self._get_body_async(request)
        form_data = await self._get_form_async(request)
        # TODO Think about files
        files = self._get_files_sync(request)

        return RequestData(
            path_params=self._get_path_params(request),
            query_params=self._get_query_params(request),
            headers=self._normalize_headers(self._get_headers(request)),
            cookies=self._get_cookies(request),
            body=self._safe_json_parse(body) or body,
            form_data=form_data,
            files=files,
        )

    @staticmethod
    def _safe_json_parse(data: Any) -> dict | None:
        """Safely parse JSON data"""
        if not data:
            return None
        try:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")
            if isinstance(data, str):
                return json.loads(data)
            return data
        except Exception:
            return None

    @staticmethod
    def _normalize_headers(headers: dict) -> dict:
        """Normalize headers to lowercase"""
        return {k.lower(): v for k, v in headers.items()} if headers else {}

    def _convert_path_for_framework(self, path: str, framework: str = "default") -> str:
        """Convert path format for specific framework"""
        pattern, replacement = self.PATH_CONVERSIONS.get(
            framework, self.PATH_CONVERSIONS["default"]
        )
        return re.sub(pattern, replacement, path)

    @staticmethod
    def is_async_endpoint(endpoint: Callable) -> bool:
        """Check if endpoint is async"""
        return inspect.iscoroutinefunction(endpoint)

    @abstractmethod
    def _get_path_params(self, request: Any) -> dict:
        """Extract path parameters"""

    @abstractmethod
    def _get_query_params(self, request: Any) -> dict:
        """Extract query parameters"""

    @abstractmethod
    def _get_headers(self, request: Any) -> dict:
        """Extract headers"""

    @abstractmethod
    def _get_cookies(self, request: Any) -> dict:
        """Extract cookies"""

    @abstractmethod
    def _get_body_sync(self, request: Any) -> bytes | str | dict:
        """Extract body synchronously"""

    @abstractmethod
    async def _get_body_async(self, request: Any) -> bytes | str | dict:
        """Extract body asynchronously"""

    @abstractmethod
    def _get_form_data_sync(self, request: Any) -> dict:
        """Extract form data synchronously"""

    @abstractmethod
    async def _get_form_async(self, request: Any) -> dict:
        """Extract form data asynchronously"""

    @abstractmethod
    def _get_files_sync(self, request: Any) -> dict:
        """Extract files synchronously"""

    @abstractmethod
    def build_framework_response(self, response: Response) -> Any:
        """Build framework-specific response object"""

    def _get_synthetic_request(self, *args, **kwargs):
        pass
