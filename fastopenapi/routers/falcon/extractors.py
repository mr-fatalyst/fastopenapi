from typing import Any

from pydantic_core import from_json

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)

_MULTIPART_CACHE_ATTR = "_fastopenapi_multipart_cache"


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
    def _parse_multipart(
        cls, request: Any
    ) -> tuple[dict, dict[str, FileUpload | list[FileUpload]]]:
        """Parse multipart stream once and cache the result on the request."""
        cached = getattr(request, _MULTIPART_CACHE_ATTR, None)
        if isinstance(cached, tuple):
            return cached

        form_data = {}
        files: dict[str, FileUpload | list[FileUpload]] = {}

        form = request.get_media()
        for part in form:
            filename = getattr(part, "secure_filename", None) or getattr(
                part, "filename", None
            )
            field_name = getattr(part, "name", filename)

            if filename:
                content = part.stream.read()
                file_upload = FileUpload(
                    filename=filename,
                    content_type=getattr(part, "content_type", None),
                    size=len(content),
                    file=content,
                )
                if field_name in files:
                    if isinstance(files[field_name], list):
                        files[field_name].append(file_upload)
                    else:
                        files[field_name] = [files[field_name], file_upload]
                else:
                    files[field_name] = file_upload
            else:
                form_data[field_name] = part.text

        result = (form_data, files)
        setattr(request, _MULTIPART_CACHE_ATTR, result)
        return result

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        ct = str(request.content_type or "").lower()

        if ct == "application/x-www-form-urlencoded":
            return request.media or {}

        if "multipart/form-data" in ct and hasattr(request, "get_media"):
            form_data, _ = cls._parse_multipart(request)
            return form_data

        return {}

    @classmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Falcon request (sync)"""
        ct = str(request.content_type or "").lower()

        if "multipart/form-data" in ct and hasattr(request, "get_media"):
            _, files = cls._parse_multipart(request)
            return files

        return {}


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
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""
        return super()._get_files(request)
