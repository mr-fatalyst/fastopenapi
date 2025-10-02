from typing import Any


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
        files: dict[str, bytes] = None,
    ):
        self.path_params = path_params or {}
        self.query_params = query_params or {}
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.body = body
        self.form_data = form_data or {}
        self.files = files or {}
