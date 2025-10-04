from typing import Any

from fastopenapi.core.types import FileUpload
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
        try:
            data = request.json or {}
        except Exception:
            data = {}
        return data

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}
        if hasattr(request, "form"):
            for key in request.form:
                values = request.form.getlist(key)
                form_data[key] = values[0] if len(values) == 1 else values
        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Sanic request"""
        files = {}
        if hasattr(request, "files"):
            for key in request.files.keys():
                file_list = request.files.getlist(key)
                uploads = []
                for sanic_file in file_list:
                    file_upload = FileUpload(
                        filename=sanic_file.name,
                        content_type=sanic_file.type,
                        size=len(sanic_file.body) if sanic_file.body else None,
                        file=sanic_file.body,
                    )
                    uploads.append(file_upload)
                files[key] = uploads[0] if len(uploads) == 1 else uploads
        return files
