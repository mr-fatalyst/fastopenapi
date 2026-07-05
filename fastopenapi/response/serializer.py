from dataclasses import dataclass

from pydantic_core import to_json

from fastopenapi.core.types import Response

# Statuses that must not carry a body or entity headers (RFC 9110)
NO_BODY_STATUSES = frozenset({204, 304})

JSON_MIMETYPES = frozenset({"application/json", "text/json"})


@dataclass
class WireResponse:
    """Finalized wire-level response: encoded body, status, complete headers.

    Adapters receive this triple and only wrap it into (or apply it to)
    their framework's response object — no serialization logic of their own.
    """

    body: bytes | None
    status: int
    headers: dict[str, str]


class ResponseSerializer:
    """Single place for response triage shared by all adapters:
    bytes/str/JSON content, default Content-Type, 204/304 semantics."""

    @classmethod
    def finalize(cls, response: Response) -> WireResponse:
        headers = dict(response.headers or {})
        content_type = cls._pop_content_type(headers)
        status = response.status_code

        if status in NO_BODY_STATUSES:
            # Custom headers (ETag, Location, ...) survive; the body and
            # entity Content-Type must not
            return WireResponse(body=None, status=status, headers=headers)

        content = response.content

        if isinstance(content, bytes):
            body = content
            content_type = content_type or "application/octet-stream"
        elif isinstance(content, str) and not cls._is_json_mimetype(content_type):
            body = content.encode("utf-8")
            content_type = content_type or "text/plain"
        else:
            body = to_json(content)
            content_type = content_type or "application/json"

        headers["Content-Type"] = content_type
        return WireResponse(body=body, status=status, headers=headers)

    @staticmethod
    def _pop_content_type(headers: dict[str, str]) -> str | None:
        """Pop Content-Type case-insensitively so it can be re-set canonically"""
        value = None
        for key in [k for k in headers if k.lower() == "content-type"]:
            value = headers.pop(key)
        return value

    @staticmethod
    def _is_json_mimetype(content_type: str | None) -> bool:
        if not content_type:
            return False
        mimetype = content_type.partition(";")[0].strip().lower()
        return mimetype in JSON_MIMETYPES or mimetype.endswith("+json")
