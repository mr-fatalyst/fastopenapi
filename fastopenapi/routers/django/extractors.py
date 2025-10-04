from typing import Any

from pydantic_core import from_json

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import (
    BaseAsyncRequestDataExtractor,
    BaseRequestDataExtractor,
)


class DjangoRequestDataExtractor(BaseRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters"""
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query parameters"""
        query_params = {}
        for key in request.GET.keys():
            values = request.GET.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    @classmethod
    def _get_headers(cls, request: Any) -> dict:
        """Extract headers"""
        return dict(request.headers)

    @classmethod
    def _get_cookies(cls, request: Any) -> dict:
        """Extract cookies"""
        return dict(request.COOKIES)

    @classmethod
    def _get_body(cls, request: Any) -> dict | list | None:
        if hasattr(request, "body") and request.body:
            try:
                return from_json(request.body.decode("utf-8"))
            except Exception:
                pass
        return {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        if hasattr(request, "POST"):
            form_data = {}
            for key in request.POST.keys():
                values = request.POST.getlist(key)
                form_data[key] = values[0] if len(values) == 1 else values
            return form_data
        return {}

    @classmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from Django request"""
        files = {}
        if hasattr(request, "FILES"):
            for key in request.FILES.keys():
                file_list = request.FILES.getlist(key)
                uploads = []
                for uploaded_file in file_list:
                    file_upload = FileUpload(
                        filename=uploaded_file.name,
                        content_type=uploaded_file.content_type,
                        size=uploaded_file.size,
                        file=uploaded_file,
                    )
                    uploads.append(file_upload)
                files[key] = uploads[0] if len(uploads) == 1 else uploads
        return files


class DjangoAsyncRequestDataExtractor(
    DjangoRequestDataExtractor,
    BaseAsyncRequestDataExtractor,
):
    @classmethod
    async def _get_body(cls, request: Any) -> bytes | str | dict:
        """Extract body"""
        return super()._get_body(request)

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return super()._get_form_data(request)

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files"""
        return super()._get_files(request)
