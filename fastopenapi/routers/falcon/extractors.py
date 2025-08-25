from typing import Any

from pydantic_core import from_json

from fastopenapi.routers.base import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)


class FalconRequestDataExtractor(BaseRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.params.keys():
            values = (
                request.params.getall(key)
                if hasattr(request.params, "getall")
                else [request.params.get(key)]
            )
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
    def _get_body(cls, request: Any) -> dict | list | None:
        ct = (request.content_type or "").lower()
        if ct == "application/json":
            try:
                body_bytes = request.bounded_stream.read()
                if body_bytes:
                    return from_json(body_bytes.decode("utf-8"))
            except Exception:
                pass
        return {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return {}

    @classmethod
    def _get_files(cls, request: Any) -> dict:
        """Extract files"""
        files = {}
        if hasattr(request, "files"):
            for name, file in request.files.items():
                # Read file content into temporary file
                content = file.stream.read()
                files[name] = content
        return files


class FalconAsyncRequestDataExtractor(
    FalconRequestDataExtractor,
    BaseAsyncRequestDataExtractor,
):
    @classmethod
    async def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""
        ct = (request.content_type or "").lower()
        if ct == "application/json":
            try:
                body_bytes = await request.bounded_stream.read()
                if body_bytes:
                    return from_json(body_bytes.decode("utf-8"))
            except Exception:
                pass
        return {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return super()._get_form_data(request)

    @classmethod
    async def _get_files(cls, request: Any) -> dict:
        """Extract files"""
        return super()._get_files(request)
