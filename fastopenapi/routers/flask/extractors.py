import io
from typing import Any

from fastopenapi.routers.base import (
    BaseRequestDataExtractor,
)


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
    def _get_files(cls, request: Any) -> dict[str, bytes]:
        """Extract files from Falcon request (WSGI/sync)."""
        files: dict[str, bytes] = {}

        content_type = (getattr(request, "content_type", "") or "").lower()
        if "multipart/form-data" not in content_type:
            return files

        get_media = getattr(request, "get_media", None)
        if get_media is None:
            return files

        form = get_media()
        for part in form:
            field_name = getattr(part, "name", None)

            filename = getattr(part, "secure_filename", None) or getattr(
                part, "filename", None
            )
            if not field_name or not filename:
                continue

            buf = io.BytesIO()
            stream = part.stream
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                buf.write(chunk)

            files[field_name] = buf.getvalue()

        return files
