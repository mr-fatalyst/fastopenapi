import inspect
import threading
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any
from weakref import WeakKeyDictionary

from fastopenapi.core.params import Depends, Security, SecurityScopes
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import (
    APIError,
    CircularDependencyError,
    DependencyError,
)


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

    def __init__(self):
        # Request-scoped cache (cleared per request)
        self._request_cache = WeakKeyDictionary()
        self._request_cache_lock = threading.RLock()

        # Execution locks per dependency function to prevent race conditions
        self._execution_locks_lock = threading.Lock()
        self._execution_locks: dict[int, threading.Lock] = {}

        # Dependency signature cache
        self._signature_cache: dict[Callable, dict] = {}

    def resolve_dependencies(
        self,
        endpoint: Callable,
        request_data: RequestData,
    ) -> dict[str, Any]:
        """
        Resolve all dependencies for an endpoint

        Args:
            endpoint: The endpoint function
            request_data: Request data container

        Returns:
            Dict mapping parameter names to resolved dependency values
        """
        # Initialize request-scoped tracking
        with self._request_cache_lock:
            if request_data not in self._request_cache:
                self._request_cache[request_data] = {
                    "resolved": {},
                    "resolving": set(),
                    "generators": [],
                }

        try:
            return self._resolve_endpoint_dependencies(endpoint, request_data)
        finally:
            # Get generators before deleting cache
            with self._request_cache_lock:
                cache = self._request_cache.get(request_data, {})
                generators = list(cache.get("generators", []))
            # Close generators (triggers finally blocks)
            for gen in generators:
                try:
                    gen.close()
                except Exception:
                    pass
            # Clean up request cache
            with self._request_cache_lock:
                if request_data in self._request_cache:
                    del self._request_cache[request_data]

    def _resolve_endpoint_dependencies(
        self, endpoint: Callable, request_data: RequestData
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
        param_name: str = None,
        param_annotation: type = None,
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
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
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
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
    ) -> Any:
        """Resolve regular Depends dependency"""
        return self._execute_dependency_function(
            dependency_func, request_data, param_name
        )

    def _execute_dependency_function(
        self,
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
        security_scopes: SecurityScopes | None = None,
    ) -> Any:
        """
        Execute dependency function with caching and circular dependency detection
        """
        cache_key = self._make_cache_key(dependency_func, request_data)
        request_cache = self._get_request_cache(request_data)

        # First check (without lock)
        hit, value = self._try_get_cached(cache_key, request_cache)
        if hit:
            return value

        # Get or create lock for this function
        func_id = id(dependency_func)
        with self._execution_locks_lock:
            if func_id not in self._execution_locks:
                self._execution_locks[func_id] = threading.Lock()
            func_lock = self._execution_locks[func_id]

        # Synchronize execution per function
        with func_lock:
            # Second check (double-checked locking pattern)
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
        dependency_func: Callable,
        kwargs: dict,
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
        dependency_func: Callable,
        kwargs: dict,
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
        dependency_func: Callable,
        kwargs: dict,
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

    def _classify_params(self, dependency_func, security_scopes):
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
        dependency_func: Callable,
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
            try:
                from fastopenapi.resolution.resolver import ParameterResolver

                # Create temporary function with only regular parameters
                def _temp():  # pragma: no cover
                    return None

                temp_sig = inspect.Signature(regular_params.values())
                temp_func = _temp
                temp_func.__signature__ = temp_sig
                temp_func.__name__ = f"temp_deps_for_{dependency_func.__name__}"

                # Resolve all regular parameters using full ParameterResolver
                resolved_regular = ParameterResolver.resolve(temp_func, request_data)
                sub_dependencies.update(resolved_regular)

            except (DependencyError, APIError):
                raise
            except Exception as e:
                # If ParameterResolver fails completely, use defaults or raise error
                for param_name, param in regular_params.items():
                    if param.default is not inspect.Parameter.empty:
                        # Use default value
                        default_val = (
                            param.default
                            if not isinstance(param.default, (Depends, Security))
                            else None
                        )
                        sub_dependencies[param_name] = default_val
                    else:
                        # Required parameter without default - this is an error
                        raise DependencyError(
                            f"Failed to resolve required parameter '{param_name}' "
                            f"for dependency '{dependency_func.__name__}'"
                        ) from e

        return sub_dependencies

    async def resolve_dependencies_async(
        self,
        endpoint: Callable,
        request_data: RequestData,
    ) -> dict[str, Any]:
        """
        Resolve all dependencies for an endpoint (async version)

        Args:
            endpoint: The endpoint function
            request_data: Request data container

        Returns:
            Dict mapping parameter names to resolved dependency values
        """
        # Initialize request-scoped tracking
        with self._request_cache_lock:
            if request_data not in self._request_cache:
                self._request_cache[request_data] = {
                    "resolved": {},
                    "resolving": set(),
                    "generators": [],
                }

        try:
            return await self._resolve_endpoint_dependencies_async(
                endpoint, request_data
            )
        finally:
            # Get generators before deleting cache
            with self._request_cache_lock:
                cache = self._request_cache.get(request_data, {})
                generators = list(cache.get("generators", []))
            # Close generators (triggers finally blocks)
            for gen in generators:
                try:
                    if inspect.isasyncgen(gen):
                        await gen.aclose()
                    else:
                        gen.close()
                except Exception:
                    pass
            # Clean up request cache
            with self._request_cache_lock:
                if request_data in self._request_cache:
                    del self._request_cache[request_data]

    async def _resolve_endpoint_dependencies_async(
        self, endpoint: Callable, request_data: RequestData
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
        param_name: str = None,
        param_annotation: type = None,
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
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
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
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
    ) -> Any:
        """Resolve regular Depends dependency (async)"""
        return await self._execute_dependency_function_async(
            dependency_func, request_data, param_name
        )

    async def _execute_dependency_function_async(
        self,
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
        security_scopes: SecurityScopes | None = None,
    ) -> Any:
        """
        Execute dependency function with caching and circular dependency detection
        """
        cache_key = self._make_cache_key(dependency_func, request_data)
        request_cache = self._get_request_cache(request_data)

        # First check (without lock)
        hit, value = self._try_get_cached(cache_key, request_cache)
        if hit:
            return value

        # Get or create lock for this function
        func_id = id(dependency_func)
        with self._execution_locks_lock:
            if func_id not in self._execution_locks:
                self._execution_locks[func_id] = threading.Lock()
            func_lock = self._execution_locks[func_id]

        # Synchronize execution per function
        with func_lock:
            # Second check (double-checked locking pattern)
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
        dependency_func: Callable,
        kwargs: dict,
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
        dependency_func: Callable,
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
            try:
                from fastopenapi.resolution.resolver import ParameterResolver

                # Create temporary function with only regular parameters
                def _temp():  # pragma: no cover
                    return None

                temp_sig = inspect.Signature(regular_params.values())
                temp_func = _temp
                temp_func.__signature__ = temp_sig
                temp_func.__name__ = f"temp_deps_for_{dependency_func.__name__}"

                # Resolve all regular parameters using full ParameterResolver
                resolved_regular = ParameterResolver.resolve(temp_func, request_data)
                sub_dependencies.update(resolved_regular)

            except (DependencyError, APIError):
                raise
            except Exception as e:
                # If ParameterResolver fails completely, use defaults or raise error
                for param_name, param in regular_params.items():
                    if param.default is not inspect.Parameter.empty:
                        # Use default value
                        default_val = (
                            param.default
                            if not isinstance(param.default, (Depends, Security))
                            else None
                        )
                        sub_dependencies[param_name] = default_val
                    else:
                        # Required parameter without default - this is an error
                        raise DependencyError(
                            f"Failed to resolve required parameter '{param_name}' "
                            f"for dependency '{dependency_func.__name__}'"
                        ) from e

        return sub_dependencies

    def _get_dependency_func(
        self,
        dependency: Depends | Security,
        param_name: str,
        param_annotation: type,
    ) -> Callable:
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
        self, dependency_func: Callable, request_data: RequestData
    ) -> tuple:
        """Create cache key for request-scoped cache"""
        return (id(dependency_func), id(request_data))

    def _get_request_cache(self, request_data: RequestData) -> dict:
        """Get cache dictionary for current request"""
        return self._request_cache[request_data]

    def _try_get_cached(
        self, cache_key: tuple, request_cache: dict
    ) -> tuple[bool, Any]:
        """Try to get cached value from request-scoped cache"""
        with self._request_cache_lock:
            resolved = request_cache["resolved"]
            if cache_key in resolved:
                return True, resolved[cache_key]
        return False, None

    def _cache_result(self, cache_key: tuple, result: Any, request_cache: dict) -> None:
        """Store result in request-scoped cache"""
        with self._request_cache_lock:
            request_cache["resolved"][cache_key] = result

    @contextmanager
    def _resolving_guard(
        self, request_cache: dict, dependency_func: Callable, param_name: str
    ):
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

    def _get_signature(self, func: Callable) -> dict[str, inspect.Parameter]:
        """Get function signature with caching"""
        if func not in self._signature_cache:
            sig = inspect.signature(func)
            self._signature_cache[func] = sig.parameters
        return self._signature_cache[func]

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics for monitoring"""
        with self._execution_locks_lock:
            locks_count = len(self._execution_locks)

        return {
            "active_requests": len(self._request_cache),
            "execution_locks": locks_count,
        }


# Global dependency resolver instance
dependency_resolver = DependencyResolver()


# Convenience functions
def resolve_dependencies(
    endpoint: Callable, request_data: RequestData
) -> dict[str, Any]:
    """Convenience function to resolve dependencies (sync)"""
    return dependency_resolver.resolve_dependencies(endpoint, request_data)


async def resolve_dependencies_async(
    endpoint: Callable, request_data: RequestData
) -> dict[str, Any]:
    """Convenience function to resolve dependencies (async)"""
    return await dependency_resolver.resolve_dependencies_async(endpoint, request_data)


def get_dependency_stats() -> dict[str, int]:
    """Get dependency resolver statistics"""
    return dependency_resolver.get_cache_stats()
