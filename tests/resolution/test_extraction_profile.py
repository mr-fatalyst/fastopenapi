from pydantic import BaseModel

from fastopenapi import Body, Cookie, Depends, File, FileUpload, Form, Query, Security
from fastopenapi.resolution.profile import (
    EXTRACT_ALL,
    ExtractionProfile,
    ExtractionProfileBuilder,
)


class Item(BaseModel):
    name: str


class TestExtractionProfile:
    def test_extract_all_defaults(self):
        assert EXTRACT_ALL == ExtractionProfile(
            needs_body=True, needs_form=True, needs_files=True
        )

    def test_plain_query_endpoint_needs_nothing(self):
        def endpoint(q: str = Query(...), limit: int = 10):
            pass

        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile == ExtractionProfile(False, False, False)

    def test_model_annotation_needs_body(self):
        def endpoint(item: Item):
            pass

        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile.needs_body
        assert not profile.needs_form
        assert not profile.needs_files

    def test_model_container_needs_body(self):
        def endpoint(items: list[Item] | None = None):
            pass

        assert ExtractionProfileBuilder.get(endpoint).needs_body

    def test_explicit_body_param_needs_body(self):
        def endpoint(payload: dict = Body(...)):
            pass

        assert ExtractionProfileBuilder.get(endpoint).needs_body

    def test_form_param_needs_form(self):
        def endpoint(name: str = Form(...)):
            pass

        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile.needs_form
        assert not profile.needs_body

    def test_file_param_needs_files(self):
        def endpoint(upload: FileUpload = File(...)):
            pass

        assert ExtractionProfileBuilder.get(endpoint).needs_files

    def test_cookie_param_needs_nothing(self):
        def endpoint(session: str = Cookie(None)):
            pass

        assert ExtractionProfileBuilder.get(endpoint) == ExtractionProfile(
            False, False, False
        )

    def test_dependency_with_form_is_transitive(self):
        def dep(csrf: str = Form(...)):
            return csrf

        def endpoint(token: str = Depends(dep)):
            pass

        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile.needs_form
        assert not profile.needs_body

    def test_nested_dependencies_are_walked(self):
        def inner(upload: FileUpload = File(...)):
            return upload

        def outer(value=Depends(inner)):
            return value

        def endpoint(data=Depends(outer)):
            pass

        assert ExtractionProfileBuilder.get(endpoint).needs_files

    def test_security_dependency_is_walked(self):
        def check(item: Item):
            return item

        def endpoint(key=Security(check)):
            pass

        assert ExtractionProfileBuilder.get(endpoint).needs_body

    def test_dependency_via_annotation(self):
        class Settings:
            pass

        def endpoint(settings: Settings = Depends()):
            pass

        # Depends() without callable uses the annotation as factory;
        # Settings() has no payload params
        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile == ExtractionProfile(False, False, False)

    def test_cyclic_dependencies_terminate(self):
        def dep_a(x=None):
            return x

        def dep_b(a=Depends(dep_a)):
            return a

        # create a cycle: a depends on b, b depends on a
        dep_a.__defaults__ = (Depends(dep_b),)

        def endpoint(value=Depends(dep_a)):
            pass

        # must not recurse forever
        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile == ExtractionProfile(False, False, False)

    def test_unresolvable_signature_falls_back_to_extract_all(self):
        # builtins like min() have no introspectable signature
        profile = ExtractionProfileBuilder.get(min)

        assert profile == ExtractionProfile(True, True, True)

    def test_profile_is_cached(self):
        def endpoint(item: Item):
            pass

        first = ExtractionProfileBuilder.get(endpoint)
        second = ExtractionProfileBuilder.get(endpoint)

        assert first is second


class TestBareDependsProfile:
    def test_bare_depends_without_annotation_is_skipped(self):
        def endpoint(x=Depends()):
            pass

        profile = ExtractionProfileBuilder.get(endpoint)

        assert profile == ExtractionProfile(False, False, False)
