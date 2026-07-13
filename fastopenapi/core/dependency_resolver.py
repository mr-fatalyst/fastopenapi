import inspect
import logging
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any
from weakref import WeakKeyDictionary

from fastopenapi.core.params import (
    Depends,
    Security,
    SecurityScopes,
    unwrap_annotated_parameter,
)
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import (
    APIError,
    CircularDependencyError,
    DependencyError,
)

logger = logging.getLogger("fastopenapi")


class DependencyResolver:
    """
    Resolves dependency injection for endpoints with support for:
    - Recursive dependency resolution
    - Request-scoped caching (dependencies resolved once per request)
    - Circular dependency detection
    - Security scopes validation
    - Thread-safe operation
    - Async and sync execution modes
    """

    def __init__(self) -> None:
        # Request-scoped cache (cleared per request)
        self._request_cache: WeakKeyDictionary[RequestData, dict[str, Any]] = (
            WeakKeyDictionary()
        )
        self._request_cache_lock = threading.RLock()

        # Dependency signature cache
        self._signature_cache: dict[
            Callable[..., Any], MappingProxyType[str, inspect.Parameter]
        ] = {}

    def resolve_dependencies(
        self,
        endpoint: Callable[..., Any],
        request_data: RequestData,
        method: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve all dependencies for an endpoint

        Generator dependencies stay open so the endpoint can use the
        yielded value; the adapter must call ``close(request_data)``
        after the endpoint returns to run their cleanup code.

        Args:
            endpoint: The endpoint function
            request_data: Request data container
            method: HTTP method of the current request

        Returns:
            Dict mapping parameter names to resolved dependency values
        """
        self._open_request_scope(request_data, method)
        return self._resolve_endpoint_dependencies(endpoint, request_data)

    def _open_request_scope(
        self, request_data: RequestData, method: str | None
    ) -> None:
        """Create the request-scoped cache entry if it does not exist yet"""
        with self._request_cache_lock:
            if request_data not in self._request_cache:
                self._request_cache[request_data] = {
                    "resolved": {},
                    "resolving": set(),
                    "generators": [],
                    "method": method,
                }

    def close(
        self, request_data: RequestData, exc: BaseException | None = None
    ) -> None:
        """
        Finish generator dependencies opened for a request

        Context-manager semantics, in reverse creation order: on success the
        code after ``yield`` executes; on the error path ``exc`` (the
        endpoint/pipeline exception) is thrown into the generator so
        ``except``/rollback blocks around ``yield`` work as in FastAPI.
        As with ``contextlib.ExitStack``, a dependency that handles the
        exception suppresses it for the dependencies finishing after it,
        and a failing teardown becomes the exception for the remaining ones.

        When the pipeline succeeded (``exc is None``) an unsuppressed
        teardown failure is re-raised so the adapter turns it into a 500;
        on the error path failures are logged without masking ``exc``.
        Drops the request cache entry; no-op when the request has none.
        """
        with self._request_cache_lock:
            cache = self._request_cache.pop(request_data, None)
        if cache is None:
            return
        current = exc
        for gen in reversed(cache["generators"]):
            try:
                if self._finish_sync_generator(gen, current):
                    current = None
            except BaseException as cleanup_exc:
                logger.exception(
                    "Cleanup of dependency '%s' failed",
                    getattr(gen, "__name__", repr(gen)),
                )
                current = cleanup_exc
        if exc is None and current is not None:
            raise current

    async def aclose(
        self, request_data: RequestData, exc: BaseException | None = None
    ) -> None:
        """Async variant of ``close`` (also handles async generators)"""
        with self._request_cache_lock:
            cache = self._request_cache.pop(request_data, None)
        if cache is None:
            return
        current = exc
        for gen in reversed(cache["generators"]):
            try:
                if inspect.isasyncgen(gen):
                    suppressed = await self._finish_async_generator(gen, current)
                else:
                    suppressed = self._finish_sync_generator(gen, current)
                if suppressed:
                    current = None
            except BaseException as cleanup_exc:
                logger.exception(
                    "Cleanup of dependency '%s' failed",
                    getattr(gen, "__name__", repr(gen)),
                )
                current = cleanup_exc
        if exc is None and current is not None:
            raise current

    def _finish_sync_generator(
        self, gen: Any, exc: BaseException | None = None
    ) -> bool:
        """Resume a generator past its ``yield`` (or throw ``exc`` into it)

        Returns True when the generator handled (suppressed) ``exc``.
        A teardown failure (an exception other than ``exc``) propagates
        to the caller, which decides whether it may be raised.
        """
        try:
            if exc is not None:
                gen.throw(exc)
            else:
                next(gen)
        except StopIteration:
            # Finished cleanly; with exc set that means it was handled
            return exc is not None
        except BaseException as cleanup_exc:
            if cleanup_exc is exc:
                # The dependency chose not to handle the endpoint error;
                # its finally blocks have already run
                return False
            raise
        logger.warning(
            "Dependency '%s' has more than one 'yield'; "
            "code after the second one is not executed",
            getattr(gen, "__name__", repr(gen)),
        )
        gen.close()
        return exc is not None

    async def _finish_async_generator(
        self, gen: Any, exc: BaseException | None = None
    ) -> bool:
        """Async variant of ``_finish_sync_generator``"""
        try:
            if exc is not None:
                await gen.athrow(exc)
            else:
                await gen.__anext__()
        except StopAsyncIteration:
            return exc is not None
        except BaseException as cleanup_exc:
            if cleanup_exc is exc:
                return False
            raise
        logger.warning(
            "Dependency '%s' has more than one 'yield'; "
            "code after the second one is not executed",
            getattr(gen, "__name__", repr(gen)),
        )
        await gen.aclose()
        return exc is not None

    def _resolve_endpoint_dependencies(
        self, endpoint: Callable[..., Any], request_data: RequestData
    ) -> dict[str, Any]:
        """Resolve dependencies for a specific endpoint"""
        dependencies = {}
        sig = self._get_signature(endpoint)

        for param_name, param in sig.items():
            if isinstance(param.default, (Depends, Security)):
                try:
                    value = self._resolve_single_dependency(
                        param.default, request_data, param_name, param.annotation
                    )
                    dependencies[param_name] = value
                except (DependencyError, APIError) as e:
                    raise e
                except Exception as e:
                    raise DependencyError(
                        f"Failed to resolve dependency '{param_name}'"
                    ) from e

        return dependencies

    def _resolve_single_dependency(
        self,
        dependency: Depends | Security,
        request_data: RequestData,
        param_name: str | None = None,
        param_annotation: type | None = None,
    ) -> Any:
        """
        Resolve a single dependency with caching and recursion

        Args:
            dependency: Depends or Security instance
            request_data: Request data container
            param_name: Parameter name for error reporting
            param_annotation: Expected return type annotation

        Returns:
            Resolved dependency value
        """
        # Get the dependency function
        dependency_func = self._get_dependency_func(
            dependency, param_name, param_annotation
        )

        # Handle Security-specific logic
        if isinstance(dependency, Security):
            return self._resolve_security_dependency(
                dependency, dependency_func, request_data, param_name
            )

        # Handle regular Depends
        return self._resolve_regular_dependency(
            dependency_func, request_data, param_name
        )

    def _resolve_security_dependency(
        self,
        security: Security,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        param_name: str | None,
    ) -> Any:
        """Resolve Security dependency, injecting SecurityScopes if requested"""
        return self._execute_dependency_function(
            dependency_func,
            request_data,
            param_name,
            security_scopes=SecurityScopes(security.scopes),
        )

    def _resolve_regular_dependency(
        self,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        param_name: str | None,
    ) -> Any:
        """Resolve regular Depends dependency"""
        return self._execute_dependency_function(
            dependency_func, request_data, param_name
        )

    def _execute_dependency_function(
        self,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        param_name: str | None,
        security_scopes: SecurityScopes | None = None,
    ) -> Any:
        """
        Execute dependency function with caching and circular dependency detection
        """
        cache_key = self._make_cache_key(dependency_func, request_data, security_scopes)
        request_cache = self._get_request_cache(request_data)

        # The cache is request-scoped and a request is handled by a single
        # thread, so no cross-request synchronization is needed here
        hit, value = self._try_get_cached(cache_key, request_cache)
        if hit:
            return value

        # Guard against circular dependencies
        with self._resolving_guard(request_cache, dependency_func, param_name):
            sub_dependencies = self._resolve_sub_dependencies(
                dependency_func, request_data, security_scopes
            )
            result = self._call_dependency(
                dependency_func, sub_dependencies or {}, request_data
            )
            self._cache_result(cache_key, result, request_cache)
            return result

    def _call_sync_generator(
        self,
        dependency_func: Callable[..., Any],
        kwargs: dict[str, Any],
        request_data: RequestData,
    ) -> Any:
        """Execute a sync generator dependency: yield value and save for cleanup."""
        gen = dependency_func(**kwargs)
        try:
            value = next(gen)
        except StopIteration:
            raise DependencyError(
                f"Generator dependency " f"'{dependency_func.__name__}' did not yield"
            )
        self._get_request_cache(request_data)["generators"].append(gen)
        return value

    async def _call_async_generator(
        self,
        dependency_func: Callable[..., Any],
        kwargs: dict[str, Any],
        request_data: RequestData,
    ) -> Any:
        """Execute an async generator dependency: yield value and save for cleanup."""
        gen = dependency_func(**kwargs)
        try:
            value = await gen.__anext__()
        except StopAsyncIteration:
            raise DependencyError(
                f"Generator dependency " f"'{dependency_func.__name__}' did not yield"
            )
        self._get_request_cache(request_data)["generators"].append(gen)
        return value

    def _call_dependency(
        self,
        dependency_func: Callable[..., Any],
        kwargs: dict[str, Any],
        request_data: RequestData,
    ) -> Any:
        """Execute the dependency function"""
        try:
            if inspect.isgeneratorfunction(dependency_func):
                return self._call_sync_generator(dependency_func, kwargs, request_data)
            return dependency_func(**kwargs)
        except (DependencyError, APIError):
            raise
        except Exception as e:
            raise DependencyError(
                f"Dependency function '{dependency_func.__name__}' failed"
            ) from e

    def _classify_params(
        self,
        dependency_func: Callable[..., Any],
        security_scopes: SecurityScopes | None,
    ) -> tuple[
        dict[str, Any], dict[str, inspect.Parameter], dict[str, inspect.Parameter]
    ]:
        """Split function params into injected, dependency, and regular."""
        sig = self._get_signature(dependency_func)
        injected = {}
        dependency_params = {}
        regular_params = {}
        for param_name, param in sig.items():
            if param.annotation is SecurityScopes:
                injected[param_name] = security_scopes or SecurityScopes()
            elif isinstance(param.default, (Depends, Security)):
                dependency_params[param_name] = param
            else:
                regular_params[param_name] = param
        return injected, dependency_params, regular_params

    def _resolve_sub_dependencies(
        self,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        security_scopes: SecurityScopes | None = None,
    ) -> dict[str, Any]:
        """
        Resolve sub-dependencies for a dependency function
        This enables recursive dependency injection
        """
        injected, dependency_params, regular_params = self._classify_params(
            dependency_func, security_scopes
        )
        sub_dependencies = dict(injected)

        # Resolve dependency parameters recursively
        for param_name, param in dependency_params.items():
            value = self._resolve_single_dependency(
                param.default, request_data, param_name, param.annotation
            )
            sub_dependencies[param_name] = value

        # Resolve regular parameters using ParameterResolver
        if regular_params:
            sub_dependencies.update(
                self._resolve_regular_params(
                    dependency_func, regular_params, request_data
                )
            )

        return sub_dependencies

    def _resolve_regular_params(
        self,
        dependency_func: Callable[..., Any],
        regular_params: dict[str, inspect.Parameter],
        request_data: RequestData,
    ) -> dict[str, Any]:
        """Resolve non-dependency parameters of a dependency function"""
        from fastopenapi.resolution.resolver import ParameterResolver

        # Dependency params follow the same method-specific rules as
        # endpoint params (e.g. bare models map to query on GET)
        cache = self._request_cache.get(request_data)
        method = cache.get("method") if cache else None

        try:
            return ParameterResolver.resolve_params(
                regular_params,
                request_data,
                method=method,
                owner=(
                    getattr(dependency_func, "__module__", "fastopenapi"),
                    getattr(dependency_func, "__qualname__", repr(dependency_func)),
                ),
            )
        except (DependencyError, APIError):
            raise
        except Exception as e:
            # If ParameterResolver fails completely, use defaults or raise error
            resolved = {}
            for param_name, param in regular_params.items():
                if param.default is not inspect.Parameter.empty:
                    # Use default value
                    resolved[param_name] = (
                        param.default
                        if not isinstance(param.default, (Depends, Security))
                        else None
                    )
                else:
                    # Required parameter without default - this is an error
                    raise DependencyError(
                        f"Failed to resolve required parameter '{param_name}' "
                        f"for dependency '{dependency_func.__name__}'"
                    ) from e
            return resolved

    async def resolve_dependencies_async(
        self,
        endpoint: Callable[..., Any],
        request_data: RequestData,
        method: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve all dependencies for an endpoint (async version)

        Generator dependencies stay open so the endpoint can use the
        yielded value; the adapter must call ``aclose(request_data)``
        after the endpoint returns to run their cleanup code.

        Args:
            endpoint: The endpoint function
            request_data: Request data container
            method: HTTP method of the current request

        Returns:
            Dict mapping parameter names to resolved dependency values
        """
        self._open_request_scope(request_data, method)
        return await self._resolve_endpoint_dependencies_async(endpoint, request_data)

    async def _resolve_endpoint_dependencies_async(
        self, endpoint: Callable[..., Any], request_data: RequestData
    ) -> dict[str, Any]:
        """Resolve dependencies for a specific endpoint (async)"""
        dependencies = {}
        sig = self._get_signature(endpoint)

        for param_name, param in sig.items():
            if isinstance(param.default, (Depends, Security)):
                try:
                    value = await self._resolve_single_dependency_async(
                        param.default, request_data, param_name, param.annotation
                    )
                    dependencies[param_name] = value
                except (DependencyError, APIError) as e:
                    raise e
                except Exception as e:
                    raise DependencyError(
                        f"Failed to resolve dependency '{param_name}'"
                    ) from e

        return dependencies

    async def _resolve_single_dependency_async(
        self,
        dependency: Depends | Security,
        request_data: RequestData,
        param_name: str | None = None,
        param_annotation: type | None = None,
    ) -> Any:
        """Resolve a single dependency with caching and recursion (async)"""
        # Get the dependency function
        dependency_func = self._get_dependency_func(
            dependency, param_name, param_annotation
        )

        # Handle Security-specific logic
        if isinstance(dependency, Security):
            return await self._resolve_security_dependency_async(
                dependency, dependency_func, request_data, param_name
            )

        # Handle regular Depends
        return await self._resolve_regular_dependency_async(
            dependency, dependency_func, request_data, param_name
        )

    async def _resolve_security_dependency_async(
        self,
        security: Security,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        param_name: str | None,
    ) -> Any:
        """Resolve Security dependency, injecting SecurityScopes if requested"""
        return await self._execute_dependency_function_async(
            dependency_func,
            request_data,
            param_name,
            security_scopes=SecurityScopes(security.scopes),
        )

    async def _resolve_regular_dependency_async(
        self,
        depends: Depends,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        param_name: str | None,
    ) -> Any:
        """Resolve regular Depends dependency (async)"""
        return await self._execute_dependency_function_async(
            dependency_func, request_data, param_name
        )

    async def _execute_dependency_function_async(
        self,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        param_name: str | None,
        security_scopes: SecurityScopes | None = None,
    ) -> Any:
        """
        Execute dependency function with caching and circular dependency detection
        """
        cache_key = self._make_cache_key(dependency_func, request_data, security_scopes)
        request_cache = self._get_request_cache(request_data)

        hit, value = self._try_get_cached(cache_key, request_cache)
        if hit:
            return value

        # Guard against circular dependencies
        with self._resolving_guard(request_cache, dependency_func, param_name):
            sub_dependencies = await self._resolve_sub_dependencies_async(
                dependency_func, request_data, security_scopes
            )
            result = await self._call_dependency_async(
                dependency_func, sub_dependencies or {}, request_data
            )
            self._cache_result(cache_key, result, request_cache)
            return result

    async def _call_dependency_async(
        self,
        dependency_func: Callable[..., Any],
        kwargs: dict[str, Any],
        request_data: RequestData,
    ) -> Any:
        """
        Execute the dependency function (async - handles both sync and async funcs)
        """
        try:
            if inspect.isasyncgenfunction(dependency_func):
                return await self._call_async_generator(
                    dependency_func, kwargs, request_data
                )
            if inspect.isgeneratorfunction(dependency_func):
                return self._call_sync_generator(dependency_func, kwargs, request_data)
            if inspect.iscoroutinefunction(dependency_func):
                return await dependency_func(**kwargs)
            return dependency_func(**kwargs)
        except (DependencyError, APIError):
            raise
        except Exception as e:
            raise DependencyError(
                f"Dependency function '{dependency_func.__name__}' failed"
            ) from e

    async def _resolve_sub_dependencies_async(
        self,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        security_scopes: SecurityScopes | None = None,
    ) -> dict[str, Any]:
        """
        Resolve sub-dependencies for a dependency function (async)
        This enables recursive dependency injection
        """
        injected, dependency_params, regular_params = self._classify_params(
            dependency_func, security_scopes
        )
        sub_dependencies = dict(injected)

        # Resolve dependency parameters recursively (async)
        for param_name, param in dependency_params.items():
            value = await self._resolve_single_dependency_async(
                param.default, request_data, param_name, param.annotation
            )
            sub_dependencies[param_name] = value

        # Resolve regular parameters using ParameterResolver
        if regular_params:
            sub_dependencies.update(
                self._resolve_regular_params(
                    dependency_func, regular_params, request_data
                )
            )

        return sub_dependencies

    def _get_dependency_func(
        self,
        dependency: Depends | Security,
        param_name: str | None,
        param_annotation: type | None,
    ) -> Callable[..., Any]:
        """Extract dependency function from Depends/Security instance"""
        dependency_func = dependency.dependency
        if dependency_func is None:
            if param_annotation and param_annotation != inspect.Parameter.empty:
                # Use type annotation as dependency function
                dependency_func = param_annotation
            else:
                raise DependencyError(
                    f"No dependency function specified for parameter '{param_name}'"
                )
        return dependency_func

    def _make_cache_key(
        self,
        dependency_func: Callable[..., Any],
        request_data: RequestData,
        security_scopes: SecurityScopes | None = None,
    ) -> tuple[int, int, tuple[str, ...]]:
        """Create cache key for request-scoped cache

        Scopes are part of the key: the same Security dependency requested
        with different scopes must be executed once per scope set.
        """
        scopes = tuple(sorted(security_scopes.scopes)) if security_scopes else ()
        return (id(dependency_func), id(request_data), scopes)

    def _get_request_cache(self, request_data: RequestData) -> dict[str, Any]:
        """Get cache dictionary for current request"""
        return self._request_cache[request_data]

    def _try_get_cached(
        self, cache_key: tuple[int, int, tuple[str, ...]], request_cache: dict[str, Any]
    ) -> tuple[bool, Any]:
        """Try to get cached value from request-scoped cache"""
        with self._request_cache_lock:
            resolved = request_cache["resolved"]
            if cache_key in resolved:
                return True, resolved[cache_key]
        return False, None

    def _cache_result(
        self,
        cache_key: tuple[int, int, tuple[str, ...]],
        result: Any,
        request_cache: dict[str, Any],
    ) -> None:
        """Store result in request-scoped cache"""
        with self._request_cache_lock:
            request_cache["resolved"][cache_key] = result

    @contextmanager
    def _resolving_guard(
        self,
        request_cache: dict[str, Any],
        dependency_func: Callable[..., Any],
        param_name: str | None,
    ) -> Iterator[None]:
        """Guard against circular dependencies"""
        resolving = request_cache["resolving"]
        if dependency_func in resolving:
            raise CircularDependencyError(
                f"Circular dependency detected for '{param_name}': "
                f"{dependency_func.__name__} -> ... -> {dependency_func.__name__}"
            )
        resolving.add(dependency_func)
        try:
            yield
        finally:
            resolving.discard(dependency_func)

    def _get_signature(
        self, func: Callable[..., Any]
    ) -> MappingProxyType[str, inspect.Parameter]:
        """Get function signature with caching"""
        cached = self._signature_cache.get(func)
        if cached is None:
            sig = inspect.signature(func)
            params = {
                name: unwrap_annotated_parameter(param)
                for name, param in sig.parameters.items()
            }
            # setdefault keeps concurrent computations consistent without a lock
            cached = self._signature_cache.setdefault(func, MappingProxyType(params))
        return cached

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics for monitoring"""
        return {
            "active_requests": len(self._request_cache),
        }


# Global dependency resolver instance
dependency_resolver = DependencyResolver()


# Convenience functions
def resolve_dependencies(
    endpoint: Callable[..., Any],
    request_data: RequestData,
    method: str | None = None,
) -> dict[str, Any]:
    """Convenience function to resolve dependencies (sync)"""
    return dependency_resolver.resolve_dependencies(endpoint, request_data, method)


async def resolve_dependencies_async(
    endpoint: Callable[..., Any],
    request_data: RequestData,
    method: str | None = None,
) -> dict[str, Any]:
    """Convenience function to resolve dependencies (async)"""
    return await dependency_resolver.resolve_dependencies_async(
        endpoint, request_data, method
    )


def get_dependency_stats() -> dict[str, int]:
    """Get dependency resolver statistics"""
    return dependency_resolver.get_cache_stats()
