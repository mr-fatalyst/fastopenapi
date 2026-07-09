"""Shared helpers for the cross-framework integration matrix."""

from urllib.parse import urlencode

MULTIPART_BOUNDARY = "fastopenapi-test-boundary-7MA4YWxkTrZu0gW"


def encode_urlencoded(fields: list[tuple[str, str]]) -> tuple[bytes, str]:
    """Encode form fields (supports repeated names) as urlencoded body."""
    return urlencode(fields).encode(), "application/x-www-form-urlencoded"


def encode_multipart(
    fields: list[tuple[str, str]] = (),
    files: list[tuple[str, str, bytes, str]] = (),
) -> tuple[bytes, str]:
    """Encode multipart/form-data body.

    fields: (name, value) pairs.
    files: (name, filename, content, content_type) tuples.
    """
    buf = bytearray()
    for name, value in fields:
        buf += (
            f"--{MULTIPART_BOUNDARY}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n'
            f"\r\n{value}\r\n"
        ).encode()
    for name, filename, content, content_type in files:
        buf += (
            f"--{MULTIPART_BOUNDARY}\r\n"
            f'Content-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        buf += content + b"\r\n"
    buf += f"--{MULTIPART_BOUNDARY}--\r\n".encode()
    return bytes(buf), f"multipart/form-data; boundary={MULTIPART_BOUNDARY}"


def assert_status(resp, expected: int) -> None:
    """Assert response status, showing the body on failure."""
    assert (
        resp.status == expected
    ), f"expected {expected}, got {resp.status}; body={resp.body[:500]!r}"
