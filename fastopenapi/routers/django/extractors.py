from typing import Any

from pydantic_core import from_json

from fastopenapi.routers.base import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)


class DjangoRequestDataExtractor(BaseRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.GET.keys():
            values = request.GET.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    @classmethod
    def _get_headers(cls, request: Any) -> dict:
        """Extract headers"""
        return dict(request.headers)

    @classmethod
    def _get_cookies(cls, request: Any) -> dict:
        """Extract cookies"""
        return dict(request.COOKIES)

    @classmethod
    def _get_body(cls, request: Any) -> dict | list | None:
        if hasattr(request, "body") and request.body:
            try:
                return from_json(request.body.decode("utf-8"))
            except Exception:
                pass
        return {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return dict(request.POST) if hasattr(request, "POST") else {}

    @classmethod
    def _get_files(cls, request: Any) -> dict:
        """Extract files"""
        return {}


class DjangoAsyncRequestDataExtractor(
    DjangoRequestDataExtractor,
    BaseAsyncRequestDataExtractor,
):
    @classmethod
    async def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""
        return super()._get_body(request)

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return super()._get_form_data(request)

    @classmethod
    async def _get_files(cls, request: Any) -> dict:
        """Extract files"""
        return super()._get_files(request)
