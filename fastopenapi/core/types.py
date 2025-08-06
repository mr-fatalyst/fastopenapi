from typing import Any, BinaryIO


class Header:
    """Marker for header parameters"""

    def __init__(self, default: Any = None, alias: str | None = None):
        self.default = default
        self.alias = alias


class Cookie:
    """Marker for cookie parameters"""

    def __init__(self, default: Any = None):
        self.default = default


class Form:
    """Marker for form data parameters"""

    def __init__(self, default: Any = None):
        self.default = default


class UploadFile:
    """File from multipart/form-data"""

    def __init__(self, filename: str, content_type: str, file: BinaryIO):
        self.filename = filename
        self.content_type = content_type
        self.file = file


class Response:
    """Custom response with headers"""

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}


class RequestData:
    """Unified request data container"""

    def __init__(
        self,
        path_params: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        cookies: dict[str, str] = None,
        body: Any = None,
        form_data: dict[str, Any] = None,
        files: dict[str, UploadFile] = None,
    ):
        self.path_params = path_params or {}
        self.query_params = query_params or {}
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.body = body
        self.form_data = form_data or {}
        self.files = files or {}
