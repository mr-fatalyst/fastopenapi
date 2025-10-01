from pydantic import BaseModel

from fastopenapi.core.types import Response
from fastopenapi.response.builder import ResponseBuilder


class ResponseModel(BaseModel):
    id: int
    message: str


class TestResponseBuilder:
    def setup_method(self):
        self.builder = ResponseBuilder()

    def test_build_simple_response(self):
        # Test building simple response
        result = "Hello, World!"
        meta = {"status_code": 200}

        response = self.builder.build(result, meta)

        assert isinstance(response, Response)
        assert response.content == "Hello, World!"
        assert response.status_code == 200
        assert response.headers == {}

    def test_build_tuple_response(self):
        # Test building response from tuple (body, status)
        result = ("Content", 201)
        meta = {}

        response = self.builder.build(result, meta)

        assert response.content == "Content"
        assert response.status_code == 201
        assert response.headers == {}

    def test_build_unknown_tuple_response(self):
        # Test building response from tuple (any, any, any, any)
        result = (1, 2, 3, 4)
        meta = {}

        response = self.builder.build(result, meta)

        assert response.content == (1, 2, 3, 4)
        assert response.status_code == 200
        assert response.headers == {}

    def test_build_tuple_response_with_headers(self):
        # Test building response from tuple (body, status, headers)
        result = ("Content", 201, {"X-Custom": "Header"})
        meta = {}

        response = self.builder.build(result, meta)

        assert response.content == "Content"
        assert response.status_code == 201
        assert response.headers == {"X-Custom": "Header"}

    def test_build_response_object(self):
        # Test building from Response object
        result = Response(content="Test", status_code=202, headers={"X-Test": "Value"})
        meta = {}

        response = self.builder.build(result, meta)

        assert response is result

    def test_serialize_pydantic_model(self):
        # Test serializing a Pydantic model response
        model = ResponseModel(id=1, message="test")
        meta = {"status_code": 200}

        response = self.builder.build(model, meta)

        assert isinstance(response.content, dict)
        assert response.content["id"] == 1
        assert response.content["message"] == "test"

    def test_serialize_list_of_models(self):
        # Test serializing a list of Pydantic models
        models = [
            ResponseModel(id=1, message="test1"),
            ResponseModel(id=2, message="test2"),
        ]
        meta = {"status_code": 200}

        response = self.builder.build(models, meta)

        assert isinstance(response.content, list)
        assert len(response.content) == 2
        assert response.content[0]["id"] == 1
        assert response.content[1]["id"] == 2

    def test_serialize_dict_with_models(self):
        # Test serializing a dict with Pydantic model values
        data = {
            "item1": ResponseModel(id=1, message="test1"),
            "item2": ResponseModel(id=2, message="test2"),
        }
        meta = {"status_code": 200}

        response = self.builder.build(data, meta)

        assert isinstance(response.content, dict)
        assert response.content["item1"]["id"] == 1
        assert response.content["item2"]["id"] == 2

    def test_serialize_primitives(self):
        # Test serializing primitive values
        assert self.builder._serialize(5) == 5
        assert self.builder._serialize("test") == "test"
        assert self.builder._serialize(True) is True
        assert self.builder._serialize(None) is None
