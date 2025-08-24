from typing import Any

from pydantic_core import from_json

from fastopenapi.routers.base import BaseAsyncRequestDataExtractor


class StarletteRequestDataExtractor(BaseAsyncRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return dict(request.path_params)

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    @classmethod
    def _get_headers(cls, request: Any) -> dict:
        """Extract headers"""
        return dict(request.headers)

    @classmethod
    def _get_cookies(cls, request: Any) -> dict:
        """Extract cookies"""
        return dict(request.cookies)

    @classmethod
    async def _get_body(cls, request: Any) -> dict | list | None:
        try:
            body_bytes = await request.body()
            if body_bytes:
                return from_json(body_bytes.decode("utf-8"))
        except Exception:
            pass
        return {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}

        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            form = await request.form()
            for key, value in form.items():
                form_data[key] = value

        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, bytes]:
        """Extract files from Falcon request (WSGI/sync)."""
        return {}
