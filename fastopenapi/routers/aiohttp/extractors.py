from typing import Any

from fastopenapi.core.types import FileUpload
from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor


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
        try:
            body_bytes = await request.read()
            if body_bytes:
                return await request.json()
        except Exception:
            pass
        return {}

    @classmethod
    async def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        form_data = {}
        content_type = request.content_type or ""

        if content_type == "application/x-www-form-urlencoded":
            post_data = await request.post()
            for key in post_data:
                values = (
                    post_data.getall(key)
                    if hasattr(post_data, "getall")
                    else [post_data[key]]
                )
                form_data[key] = values[0] if len(values) == 1 else values

        elif content_type == "multipart/form-data":
            reader = await request.multipart()
            async for part in reader:
                if part.filename:
                    continue  # Files handled separately
                form_data[part.name] = await part.text()

        return form_data

    @classmethod
    async def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract files from AioHTTP request"""
        files = {}
        content_type = request.content_type or ""

        if content_type == "multipart/form-data":
            reader = await request.multipart()
            async for part in reader:
                if not part.filename:
                    continue

                file_data = await part.read()
                file_upload = FileUpload(
                    filename=part.filename,
                    content_type=part.headers.get("Content-Type"),
                    size=len(file_data),
                    file=file_data,
                )

                if part.name in files:
                    if isinstance(files[part.name], list):
                        files[part.name].append(file_upload)
                    else:
                        files[part.name] = [files[part.name], file_upload]
                else:
                    files[part.name] = file_upload

        return files
