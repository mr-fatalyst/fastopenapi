import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from fastopenapi.core.router import BaseRouter
from fastopenapi.core.types import Response
from fastopenapi.errors.exceptions import APIError
from fastopenapi.resolution.resolver import ParameterResolver
from fastopenapi.response.builder import ResponseBuilder
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.extractors import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
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

    @abstractmethod
    def is_framework_response(self, response: Response) -> bool:
        """Check if response is framework-ready"""

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
            if self.is_framework_response(result):
                return result
            else:
                response = self.response_builder_cls.build(
                    result, endpoint.__route_meta__
                )
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
            if self.is_framework_response(result):
                return result
            else:
                response = self.response_builder_cls.build(
                    result, endpoint.__route_meta__
                )
                return self.build_framework_response(response)
        except Exception as e:
            api_error = APIError.from_exception(e, self.EXCEPTION_MAPPER)
            return self.build_framework_response(
                Response(
                    content=api_error.to_response(),
                    status_code=api_error.status_code,
                )
            )
