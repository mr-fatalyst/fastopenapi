import inspect
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

    def handle_request(self, endpoint: Callable, request: Any) -> Any:
        """Common request handling logic"""
        try:
            # Extract request data
            request_data = self.extract_request_data(request)

            # Resolve parameters
            kwargs = self.resolver.resolve(endpoint, request_data)

            # Call endpoint
            if inspect.iscoroutinefunction(endpoint):
                import asyncio

                result = asyncio.run(endpoint(**kwargs))
            else:
                result = endpoint(**kwargs)

            # Build response
            response = self.response_builder.build(result, endpoint.__route_meta__)

            # Convert to framework response
            return self.build_framework_response(response)

        except Exception as e:
            error_response = format_exception_response(e)
            return self.build_framework_response(
                Response(
                    content=error_response,
                    status_code=error_response["error"]["status"],
                )
            )
