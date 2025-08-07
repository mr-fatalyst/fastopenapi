from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from fastopenapi.core.router import BaseRouter
from fastopenapi.core.types import RequestData, Response
from fastopenapi.errors.handler import format_exception_response
from fastopenapi.resolution.resolver import ParameterResolver
from fastopenapi.response.builder import ResponseBuilder


class BaseAdapter(BaseRouter, ABC):
    """Base adapter for framework integration"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resolver = ParameterResolver()
        self.response_builder = ResponseBuilder()

    @abstractmethod
    def extract_request_data(self, request: Any) -> RequestData:
        """Extract request data from framework-specific request object"""

    @abstractmethod
    def build_framework_response(self, response: Response) -> Any:
        """Build framework-specific response object"""

    def handle_request_sync(self, endpoint: Callable, request: Any) -> Any:
        """
        Handle synchronous request.
        Used for sync endpoints in any framework.
        """
        try:
            request_data = self.extract_request_data(request)
            kwargs = self.resolver.resolve(endpoint, request_data)
            result = endpoint(**kwargs)
            response = self.response_builder.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)
        except Exception as e:
            error_response = format_exception_response(e)
            return self.build_framework_response(
                Response(
                    content=error_response,
                    status_code=error_response["error"]["status"],
                )
            )

    async def handle_request_async(self, endpoint: Callable, request: Any) -> Any:
        """
        Handle asynchronous request.
        Used for async endpoints in async-capable frameworks.
        """
        try:
            # Extract request data (might be async for some frameworks)
            if hasattr(self, "extract_request_data_async"):
                request_data = await self.extract_request_data_async(request)
            else:
                request_data = self.extract_request_data(request)

            kwargs = self.resolver.resolve(endpoint, request_data)
            result = await endpoint(**kwargs)
            response = self.response_builder.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)
        except Exception as e:
            error_response = format_exception_response(e)
            return self.build_framework_response(
                Response(
                    content=error_response, status_code=getattr(e, "status_code", 500)
                )
            )
