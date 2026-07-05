from typing import Any

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)

_MULTIPART_CACHE_ATTR = "_fastopenapi_multipart_cache"


class FalconRequestDataExtractor(BaseRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict[str, Any]:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict[str, Any]:
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
    def _get_headers(cls, request: Any) -> dict[str, Any]:
        """Extract headers"""
        return dict(request.headers)

    @classmethod
    def _get_cookies(cls, request: Any) -> dict[str, Any]:
        """Extract cookies"""
        return dict(request.cookies)

    @staticmethod
    def _mimetype(request: Any) -> str:
        """Content type without parameters such as charset or boundary"""
        return str(request.content_type or "").partition(";")[0].strip().lower()

    @staticmethod
    def _add_file(
        files: dict[str, FileUpload | list[FileUpload]],
        field_name: str,
        file_upload: FileUpload,
    ) -> None:
        existing = files.get(field_name)
        if existing is None:
            files[field_name] = file_upload
        elif isinstance(existing, list):
            existing.append(file_upload)
        else:
            files[field_name] = [existing, file_upload]

    @classmethod
    def _get_body(cls, request: Any) -> dict | list | None:
        if not cls._is_json_content(request.content_type):
            return {}
        try:
            body_bytes = request.bounded_stream.read()
        except Exception:
            return {}
        return cls._safe_json_parse(body_bytes, strict=True) or {}

    @classmethod
    def _parse_multipart(
        cls, request: Any
    ) -> tuple[dict[str, Any], dict[str, FileUpload | list[FileUpload]]]:
        """Parse multipart stream once and cache the result on the request."""
        cached = getattr(request, _MULTIPART_CACHE_ATTR, None)
        if isinstance(cached, tuple):
            return cached

        form_data: dict[str, Any] = {}
        files: dict[str, FileUpload | list[FileUpload]] = {}

        for part in request.get_media():
            field_name = getattr(part, "name", None) or ""
            if part.filename:
                # secure_filename raises for parts without a filename,
                # so it may only be read inside this branch
                filename = getattr(part, "secure_filename", None) or part.filename
                content = part.stream.read()
                file_upload = FileUpload(
                    filename=filename,
                    content_type=getattr(part, "content_type", None),
                    size=len(content),
                    file=content,
                )
                cls._add_file(files, field_name, file_upload)
            else:
                form_data[field_name] = part.text

        result = (form_data, files)
        setattr(request, _MULTIPART_CACHE_ATTR, result)
        return result

    @classmethod
    def _get_form_data(cls, request: Any) -> dict[str, Any]:
        """Extract form data"""
        mimetype = cls._mimetype(request)

        if mimetype == "application/x-www-form-urlencoded":
            return request.media or {}

        if mimetype == "multipart/form-data" and hasattr(request, "get_media"):
            form_data, _ = cls._parse_multipart(request)
            return form_data

        return {}

    @classmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Falcon request (sync)"""
        mimetype = cls._mimetype(request)

        if mimetype == "multipart/form-data" and hasattr(request, "get_media"):
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
        if not cls._is_json_content(request.content_type):
            return {}
        try:
            body_bytes = await request.bounded_stream.read()
        except Exception:
            return {}
        return cls._safe_json_parse(body_bytes, strict=True) or {}

    @classmethod
    async def _parse_multipart(
        cls, request: Any
    ) -> tuple[dict[str, Any], dict[str, FileUpload | list[FileUpload]]]:
        """Parse multipart stream once and cache the result on the request."""
        cached = getattr(request, _MULTIPART_CACHE_ATTR, None)
        if isinstance(cached, tuple):
            return cached

        form_data: dict[str, Any] = {}
        files: dict[str, FileUpload | list[FileUpload]] = {}

        form = await request.get_media()
        async for part in form:
            field_name = getattr(part, "name", None) or ""
            if part.filename:
                filename = getattr(part, "secure_filename", None) or part.filename
                content = await part.get_data()
                file_upload = FileUpload(
                    filename=filename,
                    content_type=getattr(part, "content_type", None),
                    size=len(content),
                    file=content,
                )
                cls._add_file(files, field_name, file_upload)
            else:
                form_data[field_name] = await part.get_text()

        result = (form_data, files)
        setattr(request, _MULTIPART_CACHE_ATTR, result)
        return result

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict[str, Any]:
        """Extract form data"""
        mimetype = cls._mimetype(request)

        if mimetype == "application/x-www-form-urlencoded":
            return (await request.get_media()) or {}

        if mimetype == "multipart/form-data" and hasattr(request, "get_media"):
            form_data, _ = await cls._parse_multipart(request)
            return form_data

        return {}

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""
        mimetype = cls._mimetype(request)

        if mimetype == "multipart/form-data" and hasattr(request, "get_media"):
            _, files = await cls._parse_multipart(request)
            return files

        return {}
