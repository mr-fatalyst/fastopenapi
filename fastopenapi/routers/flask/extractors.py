from typing import Any

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import BaseRequestDataExtractor


class FlaskRequestDataExtractor(BaseRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict[str, Any]:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict[str, Any]:
        """Extract query parameters"""
        query_params = {}
        for key in request.args:
            values = request.args.getlist(key)
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
    def _get_body(cls, request: Any) -> dict[str, Any] | list[Any] | None:
        if not cls._is_json_content(request.mimetype):
            return {}
        return cls._safe_json_parse(request.get_data(), strict=True) or {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict[str, Any]:
        """Extract form data"""
        if not hasattr(request, "form"):
            return {}
        form_data = {}
        for key in request.form:
            values = request.form.getlist(key)
            form_data[key] = values[0] if len(values) == 1 else values
        return form_data

    @classmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Flask request"""
        files = {}
        for key in request.files.keys():
            file_list = request.files.getlist(key)
            uploads = []
            for file_storage in file_list:
                file_upload = FileUpload(
                    filename=file_storage.filename or "unknown",
                    content_type=file_storage.content_type,
                    size=None,
                    file=file_storage,
                )
                uploads.append(file_upload)
            files[key] = uploads[0] if len(uploads) == 1 else uploads
        return files
