from typing import Any

from pydantic_core import from_json

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor

_MULTIPART_CACHE_ATTR = "_fastopenapi_multipart_cache"


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
        """Extract JSON body"""
        try:
            body_bytes = await request.read()
            if body_bytes:
                return from_json(body_bytes)
            else:
                return {}
        except Exception:
            return {}

    @classmethod
    async def _parse_multipart(
        cls, request: Any
    ) -> tuple[dict, dict[str, FileUpload | list[FileUpload]]]:
        """Parse multipart stream once and cache the result on the request."""
        cached = getattr(request, _MULTIPART_CACHE_ATTR, None)
        if isinstance(cached, tuple):
            return cached

        form_data = {}
        files: dict[str, FileUpload | list[FileUpload]] = {}

        reader = await request.multipart()
        async for part in reader:
            if part.filename:
                file_data = await part.read()
                file_upload = FileUpload(
                    filename=part.filename,
                    content_type=part.headers.get("Content-Type"),
                    size=len(file_data),
                    file=file_data,
                )
                if part.name in files:
                    existing = files[part.name]
                    if isinstance(existing, list):
                        existing.append(file_upload)
                    else:
                        files[part.name] = [existing, file_upload]
                else:
                    files[part.name] = file_upload
            else:
                form_data[part.name] = await part.text()

        result = (form_data, files)
        setattr(request, _MULTIPART_CACHE_ATTR, result)
        return result

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        content_type = request.content_type or ""

        if content_type == "application/x-www-form-urlencoded":
            post_data = await request.post()
            form_data = {}
            for key in post_data:
                values = (
                    post_data.getall(key)
                    if hasattr(post_data, "getall")
                    else [post_data[key]]
                )
                form_data[key] = values[0] if len(values) == 1 else values
            return form_data

        if content_type == "multipart/form-data":
            form_data, _ = await cls._parse_multipart(request)
            return form_data

        return {}

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from AioHTTP request"""
        content_type = request.content_type or ""

        if content_type == "multipart/form-data":
            _, files = await cls._parse_multipart(request)
            return files

        return {}
