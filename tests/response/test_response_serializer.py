from fastopenapi.core.types import Response
from fastopenapi.response.serializer import ResponseSerializer, WireResponse


class TestResponseSerializer:
    def test_dict_content_becomes_json(self):
        wire = ResponseSerializer.finalize(Response({"key": "value"}, 200, {}))

        assert isinstance(wire, WireResponse)
        assert wire.body == b'{"key":"value"}'
        assert wire.status == 200
        assert wire.headers["Content-Type"] == "application/json"

    def test_none_content_becomes_json_null(self):
        wire = ResponseSerializer.finalize(Response(None, 200, {}))

        assert wire.body == b"null"
        assert wire.headers["Content-Type"] == "application/json"

    def test_bytes_content_defaults_to_octet_stream(self):
        wire = ResponseSerializer.finalize(Response(b"binary", 200, {}))

        assert wire.body == b"binary"
        assert wire.headers["Content-Type"] == "application/octet-stream"

    def test_str_content_defaults_to_text_plain(self):
        wire = ResponseSerializer.finalize(Response("hello", 200, {}))

        assert wire.body == b"hello"
        assert wire.headers["Content-Type"] == "text/plain"

    def test_str_content_with_json_content_type_is_json_encoded(self):
        wire = ResponseSerializer.finalize(
            Response("data", 200, {"Content-Type": "application/json"})
        )

        assert wire.body == b'"data"'
        assert wire.headers["Content-Type"] == "application/json"

    def test_explicit_content_type_is_preserved(self):
        wire = ResponseSerializer.finalize(
            Response("<x/>", 200, {"Content-Type": "application/xml"})
        )

        assert wire.body == b"<x/>"
        assert wire.headers["Content-Type"] == "application/xml"

    def test_lowercase_content_type_header_is_not_duplicated(self):
        wire = ResponseSerializer.finalize(
            Response("<x/>", 200, {"content-type": "application/xml"})
        )

        assert wire.headers["Content-Type"] == "application/xml"
        assert "content-type" not in wire.headers

    def test_204_drops_body_and_content_type_but_keeps_headers(self):
        wire = ResponseSerializer.finalize(
            Response({"ignored": True}, 204, {"X-Request-Id": "req-42"})
        )

        assert wire.body is None
        assert wire.status == 204
        assert wire.headers == {"X-Request-Id": "req-42"}

    def test_304_drops_body_and_content_type_but_keeps_headers(self):
        wire = ResponseSerializer.finalize(
            Response("ignored", 304, {"ETag": '"e"', "Content-Type": "text/plain"})
        )

        assert wire.body is None
        assert wire.status == 304
        assert wire.headers == {"ETag": '"e"'}

    def test_custom_headers_survive(self):
        wire = ResponseSerializer.finalize(
            Response({"a": 1}, 201, {"X-Custom": "yes", "Location": "/a/1"})
        )

        assert wire.status == 201
        assert wire.headers["X-Custom"] == "yes"
        assert wire.headers["Location"] == "/a/1"

    def test_json_suffix_mimetype_treated_as_json(self):
        wire = ResponseSerializer.finalize(
            Response("data", 200, {"Content-Type": "application/problem+json"})
        )

        assert wire.body == b'"data"'
