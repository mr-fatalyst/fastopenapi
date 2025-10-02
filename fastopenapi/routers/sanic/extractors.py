from typing import Any

from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor


class SanicRequestDataExtractor(BaseAsyncRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for k, v in request.args.items():
            values = request.args.getlist(k)
            query_params[k] = values[0] if len(values) == 1 else values
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
        """Extract body"""
        return request.json or {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}
        if hasattr(request, "form"):
            for key in request.form:
                form_data[key] = request.form.get(key)
        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, bytes]:
        """Extract files from Quart request"""
        return {}
