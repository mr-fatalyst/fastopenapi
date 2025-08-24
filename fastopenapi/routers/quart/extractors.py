from typing import Any

from fastopenapi.routers.base import BaseAsyncRequestDataExtractor


class QuartRequestDataExtractor(BaseAsyncRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.args:
            values = request.args.getlist(key)
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
        ct = (request.mimetype or "").lower()
        data = {}
        if ct == "application/json":
            data = await request.get_json(silent=True)
        return data if data is not None else {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}

        form = await request.form
        for key in form:
            form_data[key] = form[key]

        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, bytes]:
        """Extract files from Quart request"""
        return {}
