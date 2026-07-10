import inspect
import logging
import re
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from fastopenapi.core.dependency_resolver import dependency_resolver
from fastopenapi.core.router import BaseRouter, RouteInfo
from fastopenapi.core.types import RequestData, Response
from fastopenapi.errors.exceptions import APIError, InternalServerError
from fastopenapi.resolution.profile import ExtractionProfileBuilder
from fastopenapi.resolution.resolver import ParameterResolver
from fastopenapi.response.builder import ResponseBuilder
from fastopenapi.response.serializer import ResponseSerializer, WireResponse
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.extractors import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)

logger = logging.getLogger("fastopenapi")


class BaseAdapter(BaseRouter, ABC):
    """Base adapter for framework integration"""

    # Path conversion pattern
    PATH_CONVERSIONS = (r"{(\w+)}", r"{\1}")
    EXCEPTION_MAPPER: dict[type, type] = {}
    # Sync-only adapters set this to reject async endpoints at registration;
    # async subclasses reset it to None to lift the restriction
    ASYNC_ENDPOINT_ERROR: str | None = None

    extractor_cls = BaseRequestDataExtractor
    extractor_async_cls = BaseAsyncRequestDataExtractor
    req_param_resolver_cls = ParameterResolver
    response_builder_cls = ResponseBuilder
    serializer_cls = ResponseSerializer

    _type_adapter_cache: dict[type, TypeAdapter[Any]] = {}
    _cache_lock = threading.Lock()

    def add_route(
        self,
        path: str,
        method: str,
        endpoint: Callable[..., Any],
        meta: dict[str, Any] | None = None,
    ) -> RouteInfo:
        """Register a route, rejecting async endpoints on sync-only adapters"""
        if self.ASYNC_ENDPOINT_ERROR and inspect.iscoroutinefunction(endpoint):
            raise TypeError(
                f"Async endpoint '{endpoint.__name__}' {self.ASYNC_ENDPOINT_ERROR}"
            )
        return super().add_route(path, method, endpoint, meta)

    @abstractmethod
    def build_framework_response(self, response: WireResponse) -> Any:
        """Wrap the finalized wire triple into a framework response object
        (or return it for adapters that apply it in their own handler)"""

    @abstractmethod
    def is_framework_response(self, response: Any) -> bool:
        """Check if response is framework-ready"""

    @classmethod
    def _convert_path_for_framework(cls, path: str) -> str:
        """Convert path format for specific framework"""
        pattern, replacement = cls.PATH_CONVERSIONS
        return re.sub(pattern, replacement, path)

    @classmethod
    def _get_type_adapter(cls, resp_model: Any) -> Any:
        """Get or create cached TypeAdapter"""
        if resp_model not in cls._type_adapter_cache:
            with cls._cache_lock:
                # Double-check locking
                if resp_model not in cls._type_adapter_cache:
                    cls._type_adapter_cache[resp_model] = TypeAdapter(resp_model)
        return cls._type_adapter_cache[resp_model]

    @classmethod
    def _validate_response(cls, result: Any, response_model: Any) -> Any:
        try:
            if isinstance(response_model, type) and issubclass(
                response_model, BaseModel
            ):
                if isinstance(result, response_model):
                    return result
                return response_model.model_validate(result)
            else:
                adapter = cls._get_type_adapter(response_model)
                return adapter.validate_python(result)
        except ValidationError as e:
            raise InternalServerError(
                message="Incorrect response type",
                details=f"Response validation failed: {e}",
            )

    def handle_request(
        self,
        endpoint: Callable[..., Any],
        env: RequestEnvelope,
        meta: dict[str, Any] | None = None,
    ) -> Any:
        """Handle synchronous request

        ``meta`` is the metadata of the route being served; adapters pass
        it explicitly because ``__route_meta__`` on the endpoint holds only
        the last registration (one function may serve several methods).
        """
        if meta is None:
            meta = getattr(endpoint, "__route_meta__", {})
        request_data: RequestData | None = None
        try:
            profile = ExtractionProfileBuilder.get(endpoint)
            request_data = self.extractor_cls.extract_request_data(env, profile)
            kwargs = self.req_param_resolver_cls.resolve(
                endpoint, request_data, meta.get("method")
            )
            result = endpoint(**kwargs)
            return self._finalize_result(result, meta)
        except Exception as e:
            return self.handle_exception(e)
        finally:
            # Run generator-dependency cleanup after the endpoint (and its
            # response) are done, mirroring FastAPI's yield semantics
            if request_data is not None:
                dependency_resolver.close(request_data)

    async def handle_request_async(
        self,
        endpoint: Callable[..., Any],
        env: RequestEnvelope,
        meta: dict[str, Any] | None = None,
    ) -> Any:
        """Handle asynchronous request"""
        if meta is None:
            meta = getattr(endpoint, "__route_meta__", {})
        request_data: RequestData | None = None
        try:
            profile = ExtractionProfileBuilder.get(endpoint)
            request_data = await self.extractor_async_cls.extract_request_data(
                env, profile
            )
            kwargs = await self.req_param_resolver_cls.resolve_async(
                endpoint, request_data, meta.get("method")
            )
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)
            return self._finalize_result(result, meta)
        except Exception as e:
            return self.handle_exception(e)
        finally:
            if request_data is not None:
                await dependency_resolver.aclose(request_data)

    def _finalize_result(self, result: Any, meta: dict[str, Any]) -> Any:
        """Validate and convert an endpoint result into a framework response"""
        if self.is_framework_response(result):
            return result
        response_model = meta.get("response_model")
        # Explicit Response objects and (body, status, ...) tuples opt out
        # of response-model validation
        if response_model and not isinstance(result, (Response, tuple)):
            result = self._validate_response(result, response_model)
        response = self.response_builder_cls.build(result, meta)
        wire = self.serializer_cls.finalize(response)
        return self.build_framework_response(wire)

    def handle_exception(self, exc: Exception) -> Any:
        """Convert an exception into a framework response.

        Override to customize how errors are turned into responses.
        """
        api_error = APIError.from_exception(
            exc, self.EXCEPTION_MAPPER, debug=self.debug
        )
        self.log_exception(exc, api_error)
        wire = self.serializer_cls.finalize(
            Response(
                content=api_error.to_response(),
                status_code=api_error.status_code,
            )
        )
        return self.build_framework_response(wire)

    def log_exception(self, exc: Exception, api_error: APIError) -> None:
        """Log unexpected server faults.

        Only server errors (status >= 500) are logged with a traceback;
        intentional 4xx responses are left untouched. Override to redirect
        logging (e.g. Sentry) or to silence it entirely.
        """
        if api_error.status_code >= 500:
            logger.error("Unhandled exception while processing request", exc_info=exc)
