import inspect
from typing import Any


class FileUpload:
    """Unified file upload container with framework-agnostic API"""

    __slots__ = ("filename", "content_type", "size", "_file")

    def __init__(
        self,
        filename: str,
        content_type: str | None = None,
        size: int | None = None,
        file: Any = None,
    ):
        self.filename = filename
        self.content_type = content_type or "application/octet-stream"
        self.size = size
        self._file = file

    @property
    def file(self) -> Any:
        """Access native framework file object"""
        return self._file

    def read(self) -> bytes:
        """Read entire file content (sync frameworks)"""
        if isinstance(self._file, bytes):
            return self._file
        if hasattr(self._file, "read"):
            result = self._file.read()
            if isinstance(result, bytes):
                return result
            return result.encode("utf-8") if isinstance(result, str) else result
        raise NotImplementedError("File object does not support synchronous read")

    async def aread(self) -> bytes:
        """Read entire file content (async frameworks)"""
        if isinstance(self._file, bytes):
            return self._file
        if hasattr(self._file, "read"):
            result = self._file.read()
            if inspect.iscoroutine(result):
                data = await result
                if isinstance(data, bytes):
                    return data
                return data.encode("utf-8") if isinstance(data, str) else data
            if isinstance(result, bytes):
                return result
            return result.encode("utf-8") if isinstance(result, str) else result
        raise NotImplementedError("File object does not support read")

    def __repr__(self) -> str:
        return (
            f"FileUpload(filename={self.filename!r}, "
            f"content_type={self.content_type!r}, size={self.size})"
        )


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
        files: dict[str, FileUpload | list[FileUpload]] = None,
    ):
        self.path_params = path_params or {}
        self.query_params = query_params or {}
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.body = body
        self.form_data = form_data or {}
        self.files = files or {}
