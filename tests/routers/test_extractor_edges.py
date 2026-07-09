"""Defensive edge branches of framework extractors.

These paths are unreachable through real HTTP flows (broken streams,
absent attributes, payload readers invoked with mismatched content), so
they are pinned here with lightweight fake request objects.
"""

import asyncio
from types import SimpleNamespace

from fastopenapi.routers.aiohttp.extractors import AioHttpRequestDataExtractor
from fastopenapi.routers.django.extractors import DjangoRequestDataExtractor
from fastopenapi.routers.falcon.extractors import (
    FalconAsyncRequestDataExtractor,
    FalconRequestDataExtractor,
)
from fastopenapi.routers.flask.extractors import FlaskRequestDataExtractor
from fastopenapi.routers.sanic.extractors import SanicRequestDataExtractor
from fastopenapi.routers.starlette.extractors import StarletteRequestDataExtractor
from fastopenapi.routers.tornado.extractors import TornadoRequestDataExtractor


def run(coro):
    return asyncio.run(coro)


class TestAioHttpEdges:
    def test_body_read_failure_is_dropped(self):
        class Req:
            content_type = "application/json"

            async def read(self):
                raise RuntimeError("connection reset")

        assert run(AioHttpRequestDataExtractor._get_body(Req())) == {}

    def test_form_data_ignored_for_non_form_content(self):
        req = SimpleNamespace(content_type="application/json")
        assert run(AioHttpRequestDataExtractor._get_form_data(req)) == {}

    def test_files_ignored_for_non_multipart_content(self):
        req = SimpleNamespace(content_type="application/json")
        assert run(AioHttpRequestDataExtractor._get_files(req)) == {}


class TestFalconSyncEdges:
    def test_body_read_failure_is_dropped(self):
        class Stream:
            def read(self):
                raise RuntimeError("connection reset")

        req = SimpleNamespace(content_type="application/json", bounded_stream=Stream())
        assert FalconRequestDataExtractor._get_body(req) == {}

    def test_multipart_without_get_media_yields_empty(self):
        req = SimpleNamespace(content_type="multipart/form-data")
        assert FalconRequestDataExtractor._get_form_data(req) == {}
        assert FalconRequestDataExtractor._get_files(req) == {}


class TestFalconAsyncEdges:
    def test_body_read_failure_is_dropped(self):
        class Stream:
            async def read(self):
                raise RuntimeError("connection reset")

        req = SimpleNamespace(content_type="application/json", bounded_stream=Stream())
        assert run(FalconAsyncRequestDataExtractor._get_body(req)) == {}

    def test_form_data_ignored_for_non_form_content(self):
        req = SimpleNamespace(content_type="application/json")
        assert run(FalconAsyncRequestDataExtractor._get_form_data(req)) == {}

    def test_multipart_without_get_media_yields_empty(self):
        req = SimpleNamespace(content_type="multipart/form-data")
        assert run(FalconAsyncRequestDataExtractor._get_form_data(req)) == {}
        assert run(FalconAsyncRequestDataExtractor._get_files(req)) == {}


class TestStarletteEdges:
    def test_body_read_failure_is_dropped(self):
        class Req:
            headers = {"content-type": "application/json"}

            async def body(self):
                raise RuntimeError("connection reset")

        assert run(StarletteRequestDataExtractor._get_body(Req())) == {}


class TestFlaskEdges:
    def test_form_data_without_form_attribute(self):
        assert FlaskRequestDataExtractor._get_form_data(SimpleNamespace()) == {}


class TestSanicEdges:
    def test_path_params_attribute_passthrough(self):
        req = SimpleNamespace(path_params={"a": "1"})
        assert SanicRequestDataExtractor._get_path_params(req) == {"a": "1"}

    def test_path_params_default(self):
        assert SanicRequestDataExtractor._get_path_params(SimpleNamespace()) == {}

    def test_form_data_without_form_attribute(self):
        assert run(SanicRequestDataExtractor._get_form_data(SimpleNamespace())) == {}


class TestDjangoEdges:
    def test_path_params_attribute_passthrough(self):
        req = SimpleNamespace(path_params={"a": "1"})
        assert DjangoRequestDataExtractor._get_path_params(req) == {"a": "1"}

    def test_form_data_without_post_attribute(self):
        assert DjangoRequestDataExtractor._get_form_data(SimpleNamespace()) == {}

    def test_body_without_body_attribute(self):
        assert DjangoRequestDataExtractor._get_body(SimpleNamespace()) == {}


class TestTornadoEdges:
    def test_path_params_default_when_none(self):
        req = SimpleNamespace(path_kwargs=None)
        assert TornadoRequestDataExtractor._get_path_params(req) == {}


class TestSanicMoreEdges:
    def test_body_parse_failure_without_json_content_type(self):
        class Req:
            content_type = "text/plain"

            @property
            def json(self):
                raise RuntimeError("not json")

        assert run(SanicRequestDataExtractor._get_body(Req())) == {}

    def test_files_without_files_attribute(self):
        assert run(SanicRequestDataExtractor._get_files(SimpleNamespace())) == {}


class TestStarletteMoreEdges:
    @staticmethod
    def _empty_form_request():
        class EmptyForm:
            @staticmethod
            def multi_items():
                return []

        class Req:
            headers = {"content-type": "multipart/form-data; boundary=x"}

            async def form(self):
                return EmptyForm()

        return Req()

    def test_form_data_with_no_items(self):
        req = self._empty_form_request()
        assert run(StarletteRequestDataExtractor._get_form_data(req)) == {}

    def test_files_with_no_items(self):
        req = self._empty_form_request()
        assert run(StarletteRequestDataExtractor._get_files(req)) == {}


class TestTornadoMoreEdges:
    def test_form_data_without_body_arguments(self):
        req = SimpleNamespace(body_arguments=None)
        assert run(TornadoRequestDataExtractor._get_form_data(req)) == {}

    def test_files_when_empty(self):
        req = SimpleNamespace(files=None)
        assert run(TornadoRequestDataExtractor._get_files(req)) == {}


class TestDjangoMoreEdges:
    def test_files_without_files_attribute(self):
        assert DjangoRequestDataExtractor._get_files(SimpleNamespace()) == {}


class TestStarletteContentTypeGates:
    def test_form_data_ignored_for_non_form_content(self):
        req = SimpleNamespace(headers={"content-type": "application/json"})
        assert run(StarletteRequestDataExtractor._get_form_data(req)) == {}

    def test_files_ignored_for_non_multipart_content(self):
        req = SimpleNamespace(headers={"content-type": "application/json"})
        assert run(StarletteRequestDataExtractor._get_files(req)) == {}
