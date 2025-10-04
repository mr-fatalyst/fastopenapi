from typing import Any

from pydantic_core import from_json

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor


class TornadoRequestDataExtractor(BaseAsyncRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return request.path_kwargs or {}

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.query_arguments:
            values = [v.decode("utf-8") for v in request.query_arguments[key]]
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
        """Extract body"""
        if request.body:
            try:
                json_body = from_json(request.body)
            except Exception:
                json_body = {}
        else:
            json_body = {}
        return json_body

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}
        if request.body_arguments:
            for key, values in request.body_arguments.items():
                decoded_values = [v.decode("utf-8") for v in values]
                form_data[key] = (
                    decoded_values[0] if len(decoded_values) == 1 else decoded_values
                )
        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Tornado request"""
        files = {}
        if hasattr(request, "files") and request.files:
            for key, file_list in request.files.items():
                uploads = []
                for tornado_file in file_list:
                    file_upload = FileUpload(
                        filename=tornado_file.get("filename", "unknown"),
                        content_type=tornado_file.get("content_type"),
                        size=(
                            len(tornado_file["body"])
                            if "body" in tornado_file
                            else None
                        ),
                        file=tornado_file.get("body"),
                    )
                    uploads.append(file_upload)
                files[key] = uploads[0] if len(uploads) == 1 else uploads
        return files
