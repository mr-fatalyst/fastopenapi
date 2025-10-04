import threading
import time
from unittest.mock import Mock, patch
from weakref import WeakKeyDictionary

import pytest

from fastopenapi.core.dependency_resolver import (
    DependencyResolver,
    get_dependency_stats,
    resolve_dependencies,
)
from fastopenapi.core.params import Depends, Security
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import (
    APIError,
    CircularDependencyError,
    DependencyError,
    SecurityError,
)


class TestDependencyResolver:

    def setup_method(self):
        """Setup before each test"""
        self.resolver = DependencyResolver()
        self.request_data = RequestData(
            path_params={"id": "123"},
            query_params={"page": "1"},
            headers={"authorization": "Bearer token"},
            cookies={"session": "abc"},
            body={"data": "test"},
        )

    def test_init(self):
        """Test DependencyResolver initialization"""
        resolver = DependencyResolver()
        assert isinstance(resolver._request_cache, WeakKeyDictionary)
        assert resolver._signature_cache == {}

    def test_resolve_dependencies_simple(self):
        """Test resolving simple dependency"""

        def simple_dep():
            return "dependency_result"

        def endpoint(dep: str = Depends(simple_dep)):
            return f"endpoint_{dep}"

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {"dep": "dependency_result"}

    def test_resolve_dependencies_no_dependencies(self):
        """Test endpoint without dependencies"""

        def endpoint(param: str):
            return f"endpoint_{param}"

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {}

    def test_resolve_dependencies_without_caching(self):
        """Test dependency without caching"""
        call_count = 0

        def uncached_dep():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        def endpoint(dep: str = Depends(uncached_dep)):
            return dep

        # First call
        result1 = self.resolver.resolve_dependencies(endpoint, self.request_data)
        assert result1 == {"dep": "result_1"}
        assert call_count == 1

        # Second call - should not use cache
        result2 = self.resolver.resolve_dependencies(endpoint, self.request_data)
        assert result2 == {"dep": "result_2"}
        assert call_count == 2

    def test_resolve_security_dependency_with_scopes(self):
        """Test Security dependency with scopes validation"""

        def auth_dep():
            return {"user": "john", "scopes": ["read", "write"]}

        def endpoint(user_data: dict = Security(auth_dep, scopes=["read"])):
            return user_data

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {"user_data": {"user": "john", "scopes": ["read", "write"]}}

    def test_resolve_security_dependency_insufficient_scopes(self):
        """Test Security dependency with insufficient scopes"""

        def auth_dep():
            return {"user": "john", "scopes": ["read"]}

        def endpoint(user_data: dict = Security(auth_dep, scopes=["read", "write"])):
            return user_data

        with pytest.raises(SecurityError, match="Insufficient scopes"):
            self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_resolve_security_dependency_no_scopes_in_result(self):
        """Test Security dependency when result has no scopes"""

        def auth_dep():
            return {"user": "john"}

        def endpoint(user_data: dict = Security(auth_dep, scopes=["read"])):
            return user_data

        with pytest.raises(SecurityError, match="Insufficient scopes"):
            self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_resolve_security_dependency_no_required_scopes(self):
        """Test Security dependency with no required scopes"""

        def auth_dep():
            return {"user": "john"}

        def endpoint(user_data: dict = Security(auth_dep, scopes=[])):
            return user_data

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)
        assert result == {"user_data": {"user": "john"}}

    def test_extract_scopes_from_result_dict(self):
        """Test extracting scopes from dict result"""
        result = {"scopes": ["read", "write"]}
        scopes = self.resolver._extract_scopes_from_result(result)
        assert scopes == {"read", "write"}

    def test_extract_scopes_from_result_object(self):
        """Test extracting scopes from object with scopes attribute"""
        result = Mock()
        result.scopes = ["admin", "read"]
        scopes = self.resolver._extract_scopes_from_result(result)
        assert scopes == {"admin", "read"}

    def test_extract_scopes_from_result_no_scopes(self):
        """Test extracting scopes when no scopes present"""
        result = {"user": "john"}
        scopes = self.resolver._extract_scopes_from_result(result)
        assert scopes == set()

    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""

        def dep_a(b_dep: str = None):
            if b_dep is None:
                pass
            return f"a_{b_dep or 'default'}"

        original_resolve = self.resolver._resolve_single_dependency

        def mock_resolve(
            dependency, request_data, param_name=None, param_annotation=None
        ):
            if dependency.dependency.__name__ == "dep_a":
                request_cache = self.resolver._get_request_cache(request_data)
                request_cache["resolving"].add(dependency.dependency)
                return original_resolve(
                    dependency, request_data, param_name, param_annotation
                )
            return original_resolve(
                dependency, request_data, param_name, param_annotation
            )

        with patch.object(
            self.resolver, "_resolve_single_dependency", side_effect=mock_resolve
        ):

            def endpoint(a: str = Depends(dep_a)):
                return a

            with pytest.raises(
                CircularDependencyError, match="Circular dependency detected"
            ):
                self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_nested_dependencies(self):
        """Test nested dependencies resolution"""

        def level1_dep():
            return "level1"

        def level2_dep(l1: str = Depends(level1_dep)):
            return f"level2_{l1}"

        def level3_dep(l2: str = Depends(level2_dep)):
            return f"level3_{l2}"

        def endpoint(l3: str = Depends(level3_dep)):
            return l3

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {"l3": "level3_level2_level1"}

    def test_dependency_function_failure(self):
        """Test handling of dependency function failures"""

        def failing_dep():
            raise ValueError("Dependency failed")

        def endpoint(dep: str = Depends(failing_dep)):
            return dep

        with pytest.raises(
            DependencyError, match="Dependency function 'failing_dep' failed"
        ):
            self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_dependency_api_error_propagation(self):
        """Test that APIError from dependency is propagated"""

        def failing_dep():
            raise APIError("Custom API error")

        def endpoint(dep: str = Depends(failing_dep)):
            return dep

        with pytest.raises(APIError, match="Custom API error"):
            self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_dependency_without_function(self):
        """Test dependency without function and without annotation"""

        def endpoint(dep=Depends()):
            return dep

        with pytest.raises(DependencyError, match="No dependency function specified"):
            self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_dependency_with_type_annotation_as_function(self):
        """Test using type annotation as dependency function"""

        def endpoint(dep: str = Depends()):
            return dep

        with patch.object(
            self.resolver,
            "_execute_dependency_function",
            return_value="from_annotation",
        ):
            result = self.resolver.resolve_dependencies(endpoint, self.request_data)
            assert result == {"dep": "from_annotation"}

    def test_resolve_sub_dependencies_with_regular_params(self):
        """Test resolving sub-dependencies with regular parameters"""

        def sub_dep():
            return "sub_result"

        def main_dep(sub: str = Depends(sub_dep), regular_param: str = "default"):
            return f"{sub}_{regular_param}"

        def endpoint(main: str = Depends(main_dep)):
            return main

        with patch(
            "fastopenapi.resolution.resolver.ParameterResolver"
        ) as mock_resolver:
            mock_resolver.resolve.return_value = {"regular_param": "resolved_value"}

            result = self.resolver.resolve_dependencies(endpoint, self.request_data)

            # The actual result will depend on the mocked ParameterResolver
            assert "main" in result

    def test_resolve_sub_dependencies_parameter_resolver_failure(self):
        """Test handling ParameterResolver failure in sub-dependencies"""

        def dep_with_required_param(required_param: str):
            return f"result_{required_param}"

        def endpoint(dep: str = Depends(dep_with_required_param)):
            return dep

        with patch(
            "fastopenapi.resolution.resolver.ParameterResolver"
        ) as mock_resolver:
            mock_resolver.resolve.side_effect = Exception("Resolver failed")

            with pytest.raises(
                DependencyError, match="Failed to resolve required parameter"
            ):
                self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_resolve_sub_dependencies_with_defaults(self):
        """Test sub-dependencies with default values"""

        def dep_with_defaults(param1: str = "default1", param2: int = 42):
            return f"{param1}_{param2}"

        def endpoint(dep: str = Depends(dep_with_defaults)):
            return dep

        with patch(
            "fastopenapi.resolution.resolver.ParameterResolver"
        ) as mock_resolver:
            mock_resolver.resolve.side_effect = Exception("Resolver failed")

            result = self.resolver.resolve_dependencies(endpoint, self.request_data)
            assert result == {"dep": "default1_42"}

    def test_signature_caching(self):
        """Test function signature caching"""

        def test_func(param: str):
            return param

        # First call should cache signature
        sig1 = self.resolver._get_signature(test_func)

        # Second call should use cached signature
        sig2 = self.resolver._get_signature(test_func)

        assert sig1 is sig2
        assert test_func in self.resolver._signature_cache

    def test_request_cache_cleanup(self):
        """Test request cache cleanup after resolution"""

        def test_dep():
            return "result"

        def endpoint(dep: str = Depends(test_dep)):
            return dep

        initial_cache_count = len(self.resolver._request_cache)

        self.resolver.resolve_dependencies(endpoint, self.request_data)

        # Request cache should be cleaned up
        final_cache_count = len(self.resolver._request_cache)
        assert final_cache_count == initial_cache_count

    def test_cache_key_generation(self):
        """Test cache key generation"""

        def test_func():
            return "test"

        key1 = self.resolver._make_cache_key(test_func, self.request_data)
        key2 = self.resolver._make_cache_key(test_func, self.request_data)

        assert key1 == key2
        assert isinstance(key1, tuple)
        assert len(key1) == 2

    def test_thread_safety_basic(self):
        """Test basic thread safety of cache operations"""
        call_count = 0

        def slow_dep():
            nonlocal call_count
            time.sleep(0.01)  # Small delay to increase chance of race condition
            call_count += 1
            return f"result_{call_count}"

        def endpoint(dep: str = Depends(slow_dep)):
            return dep

        results = []

        def worker():
            result = self.resolver.resolve_dependencies(endpoint, self.request_data)
            results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should get the same cached result
        unique_results = {str(r) for r in results}
        assert len(unique_results) == 1

    def test_multiple_dependencies_same_endpoint(self):
        """Test endpoint with multiple dependencies"""

        def dep1():
            return "dep1_result"

        def dep2():
            return "dep2_result"

        def dep3():
            return "dep3_result"

        def endpoint(
            d1: str = Depends(dep1), d2: str = Depends(dep2), d3: str = Security(dep3)
        ):
            return f"{d1}_{d2}_{d3}"

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {"d1": "dep1_result", "d2": "dep2_result", "d3": "dep3_result"}

    def test_dependency_returning_none(self):
        """Test dependency returning None"""

        def none_dep():
            return None

        def endpoint(dep=Depends(none_dep)):
            return dep

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {"dep": None}

    def test_dependency_with_complex_return_type(self):
        """Test dependency returning complex objects"""

        def complex_dep():
            return {"nested": {"data": [1, 2, 3]}, "value": 42}

        def endpoint(dep: dict = Depends(complex_dep)):
            return dep

        result = self.resolver.resolve_dependencies(endpoint, self.request_data)

        assert result == {"dep": {"nested": {"data": [1, 2, 3]}, "value": 42}}

    def test_resolve_endpoint_dependencies_exception_handling(self):
        """Test exception handling in _resolve_endpoint_dependencies"""

        def failing_dep():
            raise RuntimeError("Generic error")

        def endpoint(dep: str = Depends(failing_dep)):
            return dep

        with pytest.raises(
            DependencyError, match="Dependency function 'failing_dep' failed"
        ):
            self.resolver.resolve_dependencies(endpoint, self.request_data)

    def test_global_convenience_functions(self):
        """Test global convenience functions"""

        def test_dep():
            return "global_test"

        def endpoint(dep: str = Depends(test_dep)):
            return dep

        # Test global resolve function
        result = resolve_dependencies(endpoint, self.request_data)
        assert result == {"dep": "global_test"}

    def test_resolving_guard_context_manager(self):
        """Test _resolving_guard context manager behavior"""

        def test_func():
            return "test"

        request_cache = {"resolving": set()}

        # Test normal operation
        with self.resolver._resolving_guard(request_cache, test_func, "test_param"):
            assert test_func in request_cache["resolving"]

        # Function should be removed after context
        assert test_func not in request_cache["resolving"]

    def test_cache_result_storage(self):
        """Test _cache_result method"""
        cache_key = ("test", "key")
        result = "test_result"
        request_cache = {"resolved": {}}

        # Test with caching enabled
        self.resolver._cache_result(cache_key, result, request_cache)

        assert request_cache["resolved"][cache_key] == result

    def test_try_get_cached_request_scope(self):
        """Test _try_get_cached with request-scoped cache hit"""
        cache_key = ("test", "key")
        expected_result = "cached_value"
        request_cache = {"resolved": {cache_key: expected_result}}

        hit, value = self.resolver._try_get_cached(cache_key, request_cache)

        assert hit is True
        assert value == expected_result

    def test_try_get_cached_no_hit(self):
        """Test _try_get_cached with no cache hit"""
        cache_key = ("test", "key")
        request_cache = {"resolved": {}}

        hit, value = self.resolver._try_get_cached(cache_key, request_cache)

        assert hit is False
        assert value is None

    def test_cache_hit_without_lock(self):
        """Test that cached value is returned immediately without executing function"""
        call_count = 0

        def test_dep():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        def endpoint(dep: str = Depends(test_dep)):
            return dep

        # First call - should execute function
        result1 = self.resolver.resolve_dependencies(endpoint, self.request_data)
        assert result1 == {"dep": "result_1"}
        assert call_count == 1

        # Manually add value to request cache for second call
        # This simulates the "first check without lock" scenario
        new_request = RequestData(
            path_params={},
            query_params={},
            headers={},
            cookies={},
            body={},
        )

        # Initialize request cache
        with self.resolver._request_cache_lock:
            self.resolver._request_cache[new_request] = {
                "resolved": {},
                "resolving": set(),
            }

        # Pre-populate cache
        cache_key = self.resolver._make_cache_key(test_dep, new_request)
        with self.resolver._request_cache_lock:
            self.resolver._request_cache[new_request]["resolved"][
                cache_key
            ] = "cached_value"

        # Second call with new request - should hit cache without calling function
        result2 = self.resolver.resolve_dependencies(endpoint, new_request)
        assert result2 == {"dep": "cached_value"}
        assert call_count == 1  # Function was not called again

    def test_get_cache_stats(self):
        """Test get_cache_stats returns correct statistics"""
        # Initial state
        stats = self.resolver.get_cache_stats()
        assert "active_requests" in stats
        assert "execution_locks" in stats
        initial_locks = stats["execution_locks"]

        def test_dep():
            return "result"

        def endpoint(dep: str = Depends(test_dep)):
            return dep

        # Create first request
        request1 = RequestData(
            path_params={"id": "1"},
            query_params={},
            headers={},
            cookies={},
            body={},
        )

        # Initialize but don't resolve yet
        with self.resolver._request_cache_lock:
            self.resolver._request_cache[request1] = {
                "resolved": {},
                "resolving": set(),
            }

        # Check active requests increased
        stats = self.resolver.get_cache_stats()
        assert stats["active_requests"] == 1

        # Create second request
        request2 = RequestData(
            path_params={"id": "2"},
            query_params={},
            headers={},
            cookies={},
            body={},
        )

        with self.resolver._request_cache_lock:
            self.resolver._request_cache[request2] = {
                "resolved": {},
                "resolving": set(),
            }

        # Check active requests increased
        stats = self.resolver.get_cache_stats()
        assert stats["active_requests"] == 2

        # Resolve dependencies to create execution locks
        self.resolver.resolve_dependencies(endpoint, request1)

        # Check execution locks created
        stats = self.resolver.get_cache_stats()
        assert stats["execution_locks"] >= initial_locks

        # Clean up
        with self.resolver._request_cache_lock:
            if request1 in self.resolver._request_cache:
                del self.resolver._request_cache[request1]
            if request2 in self.resolver._request_cache:
                del self.resolver._request_cache[request2]

    def test_get_cache_stats_empty(self):
        """Test get_cache_stats with no active requests"""
        resolver = DependencyResolver()
        stats = resolver.get_cache_stats()

        assert stats["active_requests"] == 0
        assert stats["execution_locks"] == 0

    def test_get_cache_stats_after_request_cleanup(self):
        """Test get_cache_stats after request cache cleanup"""

        def test_dep():
            return "result"

        def endpoint(dep: str = Depends(test_dep)):
            return dep

        # Resolve dependencies
        self.resolver.resolve_dependencies(endpoint, self.request_data)

        # After resolution, request cache should be cleaned up
        stats = self.resolver.get_cache_stats()
        assert stats["active_requests"] == 0

    def test_global_get_dependency_stats(self):
        """Test global get_dependency_stats function"""

        def test_dep():
            return "global_stats_test"

        def endpoint(dep: str = Depends(test_dep)):
            return dep

        # Resolve using global function
        resolve_dependencies(endpoint, self.request_data)

        # Get stats using global function
        stats = get_dependency_stats()

        assert isinstance(stats, dict)
        assert "active_requests" in stats
        assert "execution_locks" in stats
        assert stats["active_requests"] >= 0
        assert stats["execution_locks"] >= 0

    def test_execution_locks_accumulation(self):
        """Test that execution locks are created for different functions"""

        def dep1():
            return "dep1"

        def dep2():
            return "dep2"

        def dep3():
            return "dep3"

        def endpoint(
            d1: str = Depends(dep1), d2: str = Depends(dep2), d3: str = Depends(dep3)
        ):
            return f"{d1}_{d2}_{d3}"

        initial_stats = self.resolver.get_cache_stats()
        initial_locks = initial_stats["execution_locks"]

        # Resolve dependencies - should create locks for each unique function
        self.resolver.resolve_dependencies(endpoint, self.request_data)

        final_stats = self.resolver.get_cache_stats()
        final_locks = final_stats["execution_locks"]

        # Should have created at least 3 new locks (one per dependency function)
        assert final_locks >= initial_locks + 3

    def test_request_cache_hit_performance(self):
        """Test that cache hit prevents function re-execution within same request"""
        execution_log = []

        def tracked_dep():
            execution_log.append("executed")
            return "result"

        def dep_with_subdep(sub: str = Depends(tracked_dep)):
            return f"main_{sub}"

        def endpoint(
            dep1: str = Depends(tracked_dep),
            dep2: str = Depends(dep_with_subdep),
        ):
            return f"{dep1}_{dep2}"

        # tracked_dep is used directly and as sub-dependency
        # It should only execute once within the same request
        self.resolver.resolve_dependencies(endpoint, self.request_data)

        # tracked_dep should only be called once due to request-scoped caching
        assert len(execution_log) == 1

    def test_call_dependency_success(self):
        """Test _call_dependency with successful execution"""

        def test_dep(arg1, arg2):
            return f"{arg1}_{arg2}"

        kwargs = {"arg1": "hello", "arg2": "world"}
        result = self.resolver._call_dependency(test_dep, kwargs)

        assert result == "hello_world"

    def test_call_dependency_no_args(self):
        """Test _call_dependency with no arguments"""

        def test_dep():
            return "no_args"

        result = self.resolver._call_dependency(test_dep, {})

        assert result == "no_args"

    def test_call_dependency_api_error_propagation(self):
        """Test _call_dependency propagates APIError"""

        def failing_dep():
            raise APIError("API Error")

        with pytest.raises(APIError):
            self.resolver._call_dependency(failing_dep, {})

    def test_call_dependency_dependency_error_propagation(self):
        """Test _call_dependency propagates DependencyError"""

        def failing_dep():
            raise DependencyError("Dependency Error")

        with pytest.raises(DependencyError):
            self.resolver._call_dependency(failing_dep, {})

    def test_call_dependency_generic_error_wrapping(self):
        """Test _call_dependency wraps generic exceptions"""

        def failing_dep():
            raise ValueError("Generic error")

        with pytest.raises(
            DependencyError, match="Dependency function 'failing_dep' failed"
        ):
            self.resolver._call_dependency(failing_dep, {})

    def test_dependency_error_wrapped(self):
        class DummyRequest:
            pass

        def endpoint(dep: "NotCallable" = Depends()):  # noqa: F821
            return "ok"

        resolver = DependencyResolver()
        req = DummyRequest()

        with pytest.raises(DependencyError) as exc:
            resolver.resolve_dependencies(endpoint, req)

        assert "Failed to resolve dependency 'dep'" in str(exc.value)
        assert isinstance(exc.value.__cause__, Exception)
        assert isinstance(exc.value.__cause__, TypeError)
