from typing import Any

from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor


class AioHttpRequestDataExtractor(BaseAsyncRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return dict(request.match_info)

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.query:
            values = request.query.getall(key)
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
            body_bytes = await request.read()
            if body_bytes:
                return await request.json()
        except Exception:
            pass
        return {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}

        if request.content_type == "multipart/form-data":
            reader = await request.multipart()
            async for part in reader:
                form_data[part.name] = await part.text()

        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, bytes]:
        """Extract files from AioHTTP request"""
        return {}
