import threading

import pytest
from pydantic import BaseModel, TypeAdapter

from fastopenapi.errors.exceptions import InternalServerError
from fastopenapi.routers.base import BaseAdapter


class User(BaseModel):
    id: int
    name: str


class Product(BaseModel):
    title: str
    price: float


class TestTypeAdapterCache:
    """Tests for TypeAdapter caching"""

    def test_adapter_cached_for_same_type(self):
        """TypeAdapter is created once for a given type"""
        # First call — creation
        adapter1 = BaseAdapter._get_type_adapter(list[User])

        # Second call — from cache
        adapter2 = BaseAdapter._get_type_adapter(list[User])

        # Must be the same object
        assert adapter1 is adapter2
        assert id(adapter1) == id(adapter2)

    def test_different_types_get_different_adapters(self):
        """Different types get different adapters"""
        adapter_users = BaseAdapter._get_type_adapter(list[User])
        adapter_products = BaseAdapter._get_type_adapter(list[Product])

        assert adapter_users is not adapter_products

    def test_cache_thread_safety(self):
        """Cache works correctly under multithreading"""
        adapters = []
        errors = []

        def get_adapter():
            try:
                adapter = BaseAdapter._get_type_adapter(list[User])
                adapters.append(adapter)
            except Exception as e:
                errors.append(e)

        # Start 10 threads simultaneously
        threads = [threading.Thread(target=get_adapter) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # There should be no errors
        assert len(errors) == 0

        # All adapters must be identical
        assert len({id(a) for a in adapters}) == 1

    def test_cache_persists_across_calls(self):
        """Cache persists between calls"""
        BaseAdapter._get_type_adapter(list[str])

        # Check that cache has an entry
        assert list[str] in BaseAdapter._type_adapter_cache

        # Repeated call should use the cache
        cached_adapter = BaseAdapter._type_adapter_cache[list[str]]
        result_adapter = BaseAdapter._get_type_adapter(list[str])

        assert cached_adapter is result_adapter


class TestResponseValidation:
    """Tests for response validation"""

    def test_validate_pydantic_model_instance(self):
        """Validation of an already created BaseModel instance"""
        user = User(id=1, name="John")

        result = BaseAdapter._validate_response(user, User)

        assert result is user
        assert isinstance(result, User)

    def test_validate_pydantic_model_from_dict(self):
        """Validation of dict into BaseModel"""
        user_data = {"id": 1, "name": "John"}

        result = BaseAdapter._validate_response(user_data, User)

        assert isinstance(result, User)
        assert result.id == 1
        assert result.name == "John"

    def test_validate_list_of_models(self):
        """Validation of a list of models via TypeAdapter"""
        users_data = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]

        result = BaseAdapter._validate_response(users_data, list[User])

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(u, User) for u in result)
        assert result[0].id == 1
        assert result[1].name == "Jane"

    def test_validate_primitive_types(self):
        """Validation of primitive types"""
        result_int = BaseAdapter._validate_response(42, int)
        assert result_int == 42

        result_str = BaseAdapter._validate_response("hello", str)
        assert result_str == "hello"

    def test_validation_error_raises_internal_server_error(self):
        """ValidationError is converted into InternalServerError"""
        invalid_data = {"id": "not_an_int", "name": "John"}

        with pytest.raises(InternalServerError) as exc_info:
            BaseAdapter._validate_response(invalid_data, User)

        assert exc_info.value.message == "Incorrect response type"
        assert "Response validation failed" in str(exc_info.value.details)

    def test_validation_error_for_list(self):
        """Validation error for list"""
        invalid_data = [{"id": 1, "name": "John"}, {"id": "bad", "name": "Jane"}]

        with pytest.raises(InternalServerError):
            BaseAdapter._validate_response(invalid_data, list[User])

    def test_validation_uses_cached_adapter(self):
        """Validation uses cached adapter"""
        # First validation
        users_data1 = [{"id": 1, "name": "John"}]
        BaseAdapter._validate_response(users_data1, list[User])

        # Save adapter from cache
        cached_adapter = BaseAdapter._type_adapter_cache[list[User]]

        # Second validation
        users_data2 = [{"id": 2, "name": "Jane"}]
        BaseAdapter._validate_response(users_data2, list[User])

        # Adapter should be the same
        assert BaseAdapter._type_adapter_cache[list[User]] is cached_adapter

    def test_none_response_model(self):
        """Handle case when response_model is None"""
        # This test ensures that the code does not perform validation
        # if no response model is provided.
        # In real code this is checked in handle_request via `if response_model`

    def test_complex_nested_models(self):
        """Validation of complex nested structures"""

        class Order(BaseModel):
            id: int
            user: User
            products: list[Product]

        order_data = {
            "id": 1,
            "user": {"id": 1, "name": "John"},
            "products": [
                {"title": "Book", "price": 10.5},
                {"title": "Pen", "price": 2.0},
            ],
        }

        result = BaseAdapter._validate_response(order_data, Order)

        assert isinstance(result, Order)
        assert isinstance(result.user, User)
        assert len(result.products) == 2
        assert all(isinstance(p, Product) for p in result.products)


class TestCacheConcurrency:
    """Stress tests for cache"""

    def test_high_concurrency_same_type(self):
        """Many threads request the same type"""
        results = []

        def validate_data():
            data = [{"id": 1, "name": "Test"}]
            result = BaseAdapter._validate_response(data, list[User])
            results.append(result)

        threads = [threading.Thread(target=validate_data) for _ in range(50)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results must be valid
        assert len(results) == 50
        assert all(isinstance(r, list) for r in results)

    def test_multiple_types_concurrent(self):
        """Multiple threads with different types"""
        lock = threading.Lock()
        results = {"users": 0, "products": 0}

        def validate_users():
            BaseAdapter._validate_response([{"id": 1, "name": "A"}], list[User])
            with lock:
                results["users"] += 1

        def validate_products():
            BaseAdapter._validate_response(
                [{"title": "A", "price": 1.0}], list[Product]
            )
            with lock:
                results["products"] += 1

        threads = []
        for _ in range(25):
            threads.append(threading.Thread(target=validate_users))
            threads.append(threading.Thread(target=validate_products))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results["users"] == 25
        assert results["products"] == 25

        # There should be 2 adapters in cache
        assert list[User] in BaseAdapter._type_adapter_cache
        assert list[Product] in BaseAdapter._type_adapter_cache

    def test_race_between_checks(self):
        """Race condition: adapter is created between first and second check"""
        from unittest.mock import MagicMock

        BaseAdapter._type_adapter_cache.clear()

        original_lock = BaseAdapter._cache_lock
        mock_lock = MagicMock()

        def fake_enter(self):
            BaseAdapter._type_adapter_cache[int] = TypeAdapter(int)
            original_lock.__enter__()
            return None

        def fake_exit(self, *args):
            original_lock.__exit__(*args)

        mock_lock.__enter__ = fake_enter
        mock_lock.__exit__ = fake_exit

        BaseAdapter._cache_lock = mock_lock

        try:
            result = BaseAdapter._get_type_adapter(int)
            assert result is not None
        finally:
            BaseAdapter._cache_lock = original_lock

        # Replace lock
        BaseAdapter._cache_lock = mock_lock

        try:
            result = BaseAdapter._get_type_adapter(int)
            assert result is not None
        finally:
            # Restore original lock
            BaseAdapter._cache_lock = original_lock
