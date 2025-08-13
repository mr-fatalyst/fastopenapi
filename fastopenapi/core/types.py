import os
import tempfile
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
    """File from multipart/form-data with automatic cleanup"""

    def __init__(self, filename: str, content_type: str, file: BinaryIO | bytes | str):
        self.filename = filename
        self.content_type = content_type
        self._temp_file = None

        # Handle different file types
        if isinstance(file, bytes):
            # Create temporary file for bytes
            self._temp_file = tempfile.NamedTemporaryFile(delete=False)
            self._temp_file.write(file)
            self._temp_file.seek(0)
            self.file = self._temp_file
        elif isinstance(file, str):
            # File path provided
            self.file = open(file, "rb")
        else:
            # Already a file object
            self.file = file

    def read(self, size: int = -1) -> bytes:
        """Read file content"""
        return self.file.read(size)

    def seek(self, offset: int, whence: int = 0):
        """Seek in file"""
        return self.file.seek(offset, whence)

    def close(self):
        """Close and cleanup file"""
        if hasattr(self.file, "close"):
            self.file.close()
        if self._temp_file and os.path.exists(self._temp_file.name):
            os.unlink(self._temp_file.name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        """Cleanup on garbage collection"""
        try:
            self.close()
        except Exception:
            pass


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
