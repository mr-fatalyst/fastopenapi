import inspect
import threading
from collections.abc import Callable, Sequence
from typing import Any
from weakref import WeakKeyDictionary

from fastopenapi.core.params import Depends, Security
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import (
    CircularDependencyError,
    DependencyError,
    SecurityError,
)


class DependencyResolver:
    """
    Resolves dependency injection for endpoints with support for:
    - Recursive dependency resolution
    - Caching with use_cache control
    - Circular dependency detection
    - Security scopes validation
    - Thread-safe operation
    """

    def __init__(self):
        # Thread-safe cache for dependency results
        self._cache_lock = threading.RLock()
        self._cache: dict[tuple, Any] = {}

        # Request-scoped cache (cleared per request)
        self._request_cache = WeakKeyDictionary()

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
            security_scopes: Required security scopes for the endpoint

        Returns:
            Dict mapping parameter names to resolved dependency values
        """
        # Initialize request-scoped tracking
        id(request_data)
        self._request_cache[request_data] = {
            "resolved": {},
            "resolving": set(),  # Track what we're currently resolving
        }

        try:
            return self._resolve_endpoint_dependencies(endpoint, request_data)
        finally:
            # Clean up request cache
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
        dependency_func = dependency.dependency
        if dependency_func is None:
            if param_annotation and param_annotation != inspect.Parameter.empty:
                # Use type annotation as dependency function
                dependency_func = param_annotation
            else:
                raise DependencyError(
                    f"No dependency function specified for parameter '{param_name}'"
                )

        # Handle Security-specific logic
        if isinstance(dependency, Security):
            return self._resolve_security_dependency(
                dependency, dependency_func, request_data, param_name
            )

        # Handle regular Depends
        return self._resolve_regular_dependency(
            dependency, dependency_func, request_data, param_name
        )

    def _resolve_security_dependency(
        self,
        security: Security,
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
    ) -> Any:
        """Resolve Security dependency with scope validation"""

        # Execute the dependency function first to get token data
        result = self._execute_dependency_function(
            dependency_func, request_data, security.use_cache, param_name
        )

        # Extract provided scopes from result
        provided_scopes = self._extract_scopes_from_result(result)

        # Get required scopes from Security object
        required_scopes = set(security.scopes)

        # Check if we have all required scopes
        if required_scopes and not required_scopes.issubset(provided_scopes):
            missing_scopes = required_scopes - provided_scopes
            raise SecurityError(
                f"Insufficient scopes. Missing: {', '.join(missing_scopes)}",
                required_scopes=list(required_scopes),
                provided_scopes=list(provided_scopes),
            )

        return result

    def _extract_scopes_from_result(self, result: Any) -> set[str]:
        """Extract scopes from dependency function result"""
        if isinstance(result, dict) and "scopes" in result:
            return set(result["scopes"])
        elif hasattr(result, "scopes"):
            return set(result.scopes)
        return set()

    def _resolve_regular_dependency(
        self,
        depends: Depends,
        dependency_func: Callable,
        request_data: RequestData,
        param_name: str,
    ) -> Any:
        """Resolve regular Depends dependency"""
        return self._execute_dependency_function(
            dependency_func, request_data, depends.use_cache, param_name
        )

    def _execute_dependency_function(
        self,
        dependency_func: Callable,
        request_data: RequestData,
        use_cache: bool,
        param_name: str,
    ) -> Any:
        """
        Execute dependency function with caching and circular dependency detection
        """
        # Create cache key
        cache_key = (id(dependency_func), id(request_data))

        # Check circular dependency
        request_cache = self._request_cache[request_data]
        if dependency_func in request_cache["resolving"]:
            raise CircularDependencyError(
                f"Circular dependency detected for '{param_name}': "
                f"{dependency_func.__name__} -> ... -> {dependency_func.__name__}"
            )

        # Check request-scoped cache first
        if cache_key in request_cache["resolved"]:
            return request_cache["resolved"][cache_key]

        # Check global cache if use_cache is enabled
        if use_cache:
            with self._cache_lock:
                if cache_key in self._cache:
                    result = self._cache[cache_key]
                    request_cache["resolved"][cache_key] = result
                    return result

        # Mark as currently resolving
        request_cache["resolving"].add(dependency_func)

        try:
            # Resolve sub-dependencies first
            sub_dependencies = self._resolve_sub_dependencies(
                dependency_func, request_data
            )

            # Execute the dependency function
            try:
                if sub_dependencies:
                    result = dependency_func(**sub_dependencies)
                else:
                    result = dependency_func()
            except Exception as e:
                raise DependencyError(
                    f"Dependency function '{dependency_func.__name__}' failed"
                ) from e

            # Cache the result
            request_cache["resolved"][cache_key] = result

            if use_cache:
                with self._cache_lock:
                    self._cache[cache_key] = result

            return result

        finally:
            # Remove from resolving set
            request_cache["resolving"].discard(dependency_func)

    def _resolve_sub_dependencies(
        self, dependency_func: Callable, request_data: RequestData
    ) -> dict[str, Any]:
        """
        Resolve sub-dependencies for a dependency function
        This enables recursive dependency injection
        """
        sig = self._get_signature(dependency_func)
        sub_dependencies = {}

        # Import here to avoid circular imports
        from fastopenapi.resolution.resolver import ParameterResolver

        for param_name, param in sig.items():
            if isinstance(param.default, (Depends, Security)):
                # Recursive dependency resolution
                value = self._resolve_single_dependency(
                    param.default, request_data, param_name, param.annotation
                )
                sub_dependencies[param_name] = value
            else:
                # Use ParameterResolver for regular parameters
                try:
                    # Create a mini-endpoint just for parameter resolution
                    def dummy_endpoint(**kwargs):
                        pass

                    # Copy the parameter to dummy endpoint
                    dummy_sig = inspect.Signature([param.replace(name=param_name)])
                    dummy_endpoint.__signature__ = dummy_sig

                    resolved_params = ParameterResolver.resolve(
                        dummy_endpoint, request_data
                    )
                    if param_name in resolved_params:
                        sub_dependencies[param_name] = resolved_params[param_name]

                except Exception as e:
                    # If parameter resolution fails, check if it's optional
                    if param.default is not inspect.Parameter.empty:
                        # Use default value
                        default_val = (
                            param.default
                            if not isinstance(param.default, (Depends, Security))
                            else None
                        )
                        sub_dependencies[param_name] = default_val
                    else:
                        raise DependencyError(
                            f"Failed to resolve parameter '{param_name}' "
                            f"for dependency '{dependency_func.__name__}'"
                        ) from e

        return sub_dependencies

    def _get_signature(self, func: Callable) -> dict[str, inspect.Parameter]:
        """Get function signature with caching"""
        if func not in self._signature_cache:
            sig = inspect.signature(func)
            self._signature_cache[func] = sig.parameters
        return self._signature_cache[func]

    def clear_cache(self):
        """Clear the global dependency cache"""
        with self._cache_lock:
            self._cache.clear()

    def clear_function_cache(self, dependency_func: Callable):
        """Clear cache for a specific dependency function"""
        with self._cache_lock:
            keys_to_remove = [
                key for key in self._cache.keys() if key[0] == id(dependency_func)
            ]
            for key in keys_to_remove:
                del self._cache[key]

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics for monitoring"""
        with self._cache_lock:
            return {
                "cache_size": len(self._cache),
                "active_requests": len(self._request_cache),
            }


# Global dependency resolver instance
dependency_resolver = DependencyResolver()


# Convenience functions
def resolve_dependencies(
    endpoint: Callable, request_data: RequestData, security_scopes: Sequence[str] = None
) -> dict[str, Any]:
    """Convenience function to resolve dependencies"""
    return dependency_resolver.resolve_dependencies(
        endpoint, request_data, security_scopes
    )


def clear_dependency_cache():
    """Clear the global dependency cache"""
    dependency_resolver.clear_cache()


def get_dependency_stats() -> dict[str, int]:
    """Get dependency resolver statistics"""
    return dependency_resolver.get_cache_stats()
