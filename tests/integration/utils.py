"""Shared helpers for the cross-framework integration matrix."""

import asyncio
import sys
from urllib.parse import urlencode

MULTIPART_BOUNDARY = "fastopenapi-test-boundary-7MA4YWxkTrZu0gW"


# --- WORKAROUND (delete when Python 3.10 support is dropped) -----------------
# falcon.testing's sync simulate_*() drives ASGI apps via async_to_sync().
# On Python < 3.11 there is no asyncio.Runner, so falcon falls back to a shim
# (falcon/util/sync.py::_DummyRunner) that takes the loop from the global
# asyncio policy.  Any earlier asyncio.run() in the process (pytest-asyncio,
# the quart/sanic/django-async clients) leaves the policy with _set_called=True
# and no loop, so the shim's get_event_loop() raises "There is no current
# event loop in thread 'MainThread'".
#
# This repairs the policy right before falcon needs it.  Call sites:
#   - tests/integration/clients.py::FalconAsyncClient.send
#   - tests/routers/falcon/async_router/test_falcon_router.py (autouse fixture)
# Remove the helper and both call sites together.
def ensure_policy_event_loop() -> None:
    if sys.version_info >= (3, 11):
        return  # falcon uses asyncio.Runner, which owns its loop
    policy = asyncio.get_event_loop_policy()
    try:
        loop = policy.get_event_loop()
    except RuntimeError:
        loop = None
    # A closed loop is as unusable as a missing one: falcon would recreate its
    # runner but get the same closed loop back from the policy.
    if loop is None or loop.is_closed():
        policy.set_event_loop(policy.new_event_loop())


# --- end workaround -----------------------------------------------------------


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
