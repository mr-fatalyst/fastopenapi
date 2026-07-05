from typing import Any

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor


class StarletteRequestDataExtractor(BaseAsyncRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict[str, Any]:
        """Extract path parameters"""
        return dict(request.path_params)

    @classmethod
    def _get_query_params(cls, request: Any) -> dict[str, Any]:
        """Extract query parameters"""
        query_params = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
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

    @classmethod
    async def _get_body(cls, request: Any) -> dict | list | None:
        try:
            body_bytes = await request.body()
        except Exception:
            return {}
        strict = cls._is_json_content(request.headers.get("content-type", ""))
        return cls._safe_json_parse(body_bytes, strict=strict) or {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict[str, Any]:
        """Extract form data"""
        form_data = {}
        content_type = request.headers.get("content-type", "")

        if (
            "multipart/form-data" in content_type
            or "application/x-www-form-urlencoded" in content_type
        ):
            form = await request.form()
            for key, value in form.items():
                if not hasattr(value, "filename"):
                    form_data[key] = value

        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Starlette request"""
        files: dict[str, FileUpload | list[FileUpload]] = {}
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            form = await request.form()
            for key, value in form.items():
                if hasattr(value, "filename"):
                    file_upload = FileUpload(
                        filename=value.filename,
                        content_type=value.content_type,
                        size=value.size if hasattr(value, "size") else None,
                        file=value,
                    )

                    if key in files:
                        if isinstance(files[key], list):
                            files[key].append(file_upload)
                        else:
                            files[key] = [files[key], file_upload]
                    else:
                        files[key] = file_upload

        return files
