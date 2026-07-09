"""Shared endpoint definitions for the cross-framework integration matrix.

The same routes are registered on every framework router. All endpoints are
plain sync functions so they are valid for both sync and async adapters.
"""

from typing import Annotated

from pydantic import BaseModel

from fastopenapi import (
    Body,
    Cookie,
    Depends,
    File,
    FileUpload,
    Form,
    Header,
    Query,
    Response,
    Security,
    SecurityScopes,
)
from fastopenapi.errors import AuthenticationError


class EchoItem(BaseModel):
    name: str
    price: float = 1.0


class DeleteFilter(BaseModel):
    ids: list[int]


class ItemOut(BaseModel):
    id: int
    name: str


class SearchFilter(BaseModel):
    term: str
    limit: int = 10


# --- dependencies used by the DI scenarios -------------------------------


def paging(page: int = Query(1), per_page: int = Query(10)) -> dict:
    return {"page": page, "per_page": per_page}


def outer_paging(paging_data: dict = Depends(paging)) -> dict:
    return {"wrapped": paging_data}


def form_token(csrf: str = Form(...)) -> str:
    return csrf


def cookie_session(session: str = Cookie(None)) -> str | None:
    return session


def resource_dependency():
    yield "gen-value"


def check_api_key(x_api_key: str = Header(None)) -> str:
    if x_api_key != "secret-key":
        raise AuthenticationError("Invalid API key")
    return x_api_key


def db_session():
    session = {"open": True}
    try:
        yield session
    finally:
        session["open"] = False


def scoped_access(security_scopes: SecurityScopes) -> list:
    return list(security_scopes.scopes)


def search_filters(filters: SearchFilter) -> SearchFilter:
    return filters


async def async_source() -> str:
    return "async-dep"


async def async_resource():
    yield "async-gen"


def register_routes(router) -> None:  # noqa: C901
    """Register the shared route set on a fastopenapi router."""

    @router.get("/ping")
    def ping():
        return {"ping": "pong"}

    @router.get("/query-multi")
    def query_multi(tags: list[str] = Query(None)):
        return {"tags": tags}

    @router.post("/form")
    def form_endpoint(name: str = Form(...), tags: list[str] = Form(None)):
        return {"name": name, "tags": tags}

    @router.post("/upload")
    def upload(file: FileUpload = File(...)):
        return {"filename": file.filename, "content_type": file.content_type}

    @router.post("/upload-multi")
    def upload_multi(files: list[FileUpload] = File(...)):
        return {"count": len(files), "filenames": [f.filename for f in files]}

    @router.post("/upload-mixed")
    def upload_mixed(file: FileUpload = File(...), caption: str = Form(...)):
        return {"filename": file.filename, "caption": caption}

    @router.get("/cookie")
    def cookie_endpoint(session: str = Cookie(None)):
        return {"session": session}

    @router.get("/header")
    def header_endpoint(x_token: str = Header(None)):
        return {"x_token": x_token}

    @router.post("/json-echo")
    def json_echo(item: EchoItem):
        return {"name": item.name, "price": item.price}

    @router.post("/json-list")
    def json_list(items: list[EchoItem] = Body(...)):
        return {"names": [i.name for i in items]}

    @router.post("/json-list-plain")
    def json_list_plain(items: list[EchoItem]):
        return {"names": [i.name for i in items]}

    @router.post("/json-optional")
    def json_optional(item: EchoItem | None = None):
        return {"received": None if item is None else item.name}

    @router.delete("/items")
    def delete_items(filters: DeleteFilter):
        return {"ids": filters.ids}

    @router.get("/annotated")
    def annotated_endpoint(
        q: Annotated[str, Query(alias="q-alias")] = "default",
        limit: Annotated[int, Query(ge=1)] = 1,
    ):
        return {"q": q, "limit": limit}

    @router.get("/head-me")
    def head_me():
        return {"ok": True}

    @router.get("/no-content", status_code=204)
    def no_content():
        return Response(
            content=None, status_code=204, headers={"X-Request-Id": "req-42"}
        )

    @router.get("/not-modified")
    def not_modified():
        return None, 304, {"ETag": '"etag-42"'}

    @router.get("/boom")
    def boom():
        raise RuntimeError("SECRET-DETAIL-boom")

    # --- CRUD / path params / response_model ------------------------------

    @router.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"id": item_id, "type": type(item_id).__name__}

    @router.post("/items", status_code=201, response_model=ItemOut)
    def create_item(item: EchoItem):
        return ItemOut(id=1, name=item.name)

    @router.put("/items/{item_id}", response_model=ItemOut)
    def update_item(item_id: int, item: EchoItem):
        return ItemOut(id=item_id, name=item.name)

    @router.patch("/items/{item_id}")
    def patch_item(item_id: int, item: EchoItem):
        return {"id": item_id, "patched": item.name}

    @router.get("/items-list", response_model=list[ItemOut])
    def list_items():
        return [ItemOut(id=1, name="a"), ItemOut(id=2, name="b")]

    @router.get("/bad-response", response_model=ItemOut)
    def bad_response():
        # Violates the declared response_model -> 500 Incorrect response type
        return {"unexpected": True}

    # --- content types / tuple responses ----------------------------------

    @router.get("/binary")
    def binary():
        return b"\x00\x01BINARY"

    @router.get("/plain-text")
    def plain_text():
        return "just text"

    @router.get("/html")
    def html():
        return "<h1>hi</h1>", 200, {"Content-Type": "text/html"}

    @router.get("/xml")
    def xml():
        return "<item>1</item>", 200, {"Content-Type": "application/xml"}

    @router.get("/echo-headers")
    def echo_headers(x_request_id: str = Header(None)):
        return (
            {"received": x_request_id},
            200,
            {"X-Echo-Id": x_request_id or "none"},
        )

    # --- dependency injection ----------------------------------------------

    @router.get("/di-query")
    def di_query(p: dict = Depends(paging)):
        return p

    @router.get("/di-nested")
    def di_nested(data: dict = Depends(outer_paging)):
        return data

    @router.post("/di-form")
    def di_form(csrf: str = Depends(form_token)):
        return {"csrf": csrf}

    @router.get("/di-cookie")
    def di_cookie(session: str | None = Depends(cookie_session)):
        return {"session": session}

    @router.get("/di-generator")
    def di_generator(value: str = Depends(resource_dependency)):
        return {"value": value}

    @router.get("/di-yield-open")
    def di_yield_open(db: dict = Depends(db_session)):
        # The yielded resource must still be open while the endpoint runs;
        # cleanup happens after the response is built
        return {"open": db["open"]}

    @router.get("/di-scopes")
    def di_scopes(
        read: list = Security(scoped_access, scopes=["read"]),
        admin: list = Security(scoped_access, scopes=["admin"]),
    ):
        return {"read": read, "admin": admin}

    @router.get("/di-model-query")
    def di_model_query(filters: SearchFilter = Depends(search_filters)):
        # Bare model inside a dependency follows GET semantics: query params
        return {"term": filters.term, "limit": filters.limit}

    @router.get("/secure")
    def secure(key: str = Security(check_api_key)):
        return {"authorized": True}

    @router.head("/health")
    def health_head():
        # Explicit HEAD endpoint: headers only, no body by definition
        return None, 200, {"X-Health": "ok"}

    @router.options("/opts")
    def opts():
        return None, 204, {"Allow": "GET, OPTIONS"}

    @router.get("/things/{category}/{thing_id}")
    def multi_path(category: str, thing_id: int):
        return {"category": category, "thing_id": thing_id}

    @router.get("/query-required")
    def query_required(q: str):
        return {"q": q}

    @router.get("/search")
    def search(filters: SearchFilter):
        # GET + model: fields are mapped onto query parameters
        return {"term": filters.term, "limit": filters.limit}

    @router.post("/embedded")
    def embedded(a: int = Body(...), b: str = Body("default-b")):
        # two Body params are embedded by name
        return {"a": a, "b": b}

    # async endpoints exist only on routers that accept them
    if router.ASYNC_ENDPOINT_ERROR is None:
        _register_async_routes(router)


def _register_async_routes(router) -> None:
    """Async endpoints: the `await endpoint(...)` pipeline branch."""

    @router.get("/async-ping")
    async def async_ping():
        return {"ping": "async-pong"}

    @router.post("/async-echo")
    async def async_echo(item: EchoItem, source: str = Depends(async_source)):
        return {"name": item.name, "source": source}

    @router.get("/async-gen")
    async def async_gen(value: str = Depends(async_resource)):
        return {"value": value}
