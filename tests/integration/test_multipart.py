import pytest

from tests.integration.utils import assert_status, encode_multipart

pytestmark = pytest.mark.integration


def test_single_file_upload(client):
    body, ct = encode_multipart(
        files=[("file", "hello.txt", b"hi there", "text/plain")]
    )
    resp = client.post("/upload", content=body, content_type=ct)
    assert_status(resp, 200)
    data = resp.json()
    assert data["filename"] == "hello.txt"


def test_multiple_files_same_field(client):
    # three files so list-append merge paths are exercised too
    body, ct = encode_multipart(
        files=[
            ("files", "a.txt", b"aaa", "text/plain"),
            ("files", "b.txt", b"bbb", "text/plain"),
            ("files", "c.txt", b"ccc", "text/plain"),
        ]
    )
    resp = client.post("/upload-multi", content=body, content_type=ct)
    assert_status(resp, 200)
    data = resp.json()
    assert data["count"] == 3
    assert sorted(data["filenames"]) == ["a.txt", "b.txt", "c.txt"]


def test_file_with_text_fields(client):
    body, ct = encode_multipart(
        fields=[("caption", "my caption")],
        files=[("file", "photo.png", b"\x89PNG-fake", "image/png")],
    )
    resp = client.post("/upload-mixed", content=body, content_type=ct)
    assert_status(resp, 200)
    assert resp.json() == {"filename": "photo.png", "caption": "my caption"}
