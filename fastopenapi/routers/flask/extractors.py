from typing import Any

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import BaseRequestDataExtractor


class FlaskRequestDataExtractor(BaseRequestDataExtractor):
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
    def _get_body(cls, request: Any) -> dict | list | None:
        ct = (request.mimetype or "").lower()
        data = {}
        if ct == "application/json":
            data = request.get_json(silent=True)
        return data if data is not None else {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return dict(request.form) if hasattr(request, "form") else {}

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
