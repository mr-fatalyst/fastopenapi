from http import HTTPStatus

from quart import abort

from fastopenapi.routers import QuartRouter

from ...schemas.authors import (
    AuthorSchema,
    CreateAuthorSchema,
    FilterAuthorSchema,
    UpdateAuthorSchema,
)
from ...services.authors import AuthorService

author_service = AuthorService()

router = QuartRouter()


@router.post("/authors", tags=["Authors"], status_code=201, response_model=AuthorSchema)
async def create_author(body: CreateAuthorSchema) -> AuthorSchema:
    return author_service.create_author(body)


@router.get("/authors/{author_id}", tags=["Authors"], response_model=AuthorSchema)
async def get_author(author_id: int) -> AuthorSchema:
    author = author_service.get_author(author_id)
    if not author:
        abort(HTTPStatus.NOT_FOUND)
    return author


@router.get("/authors/", tags=["Authors"], response_model=list[AuthorSchema])
async def get_authors(body: FilterAuthorSchema) -> list[AuthorSchema]:
    return author_service.get_authors(body)


@router.delete("/authors/{author_id}", tags=["Authors"], status_code=204)
async def delete_author(author_id: int) -> None:
    author = author_service.delete_author(author_id)
    if not author:
        abort(HTTPStatus.NOT_FOUND)
    return None


@router.patch("/authors/{author_id}", tags=["Authors"], response_model=AuthorSchema)
async def update_author(author_id: int, body: UpdateAuthorSchema) -> AuthorSchema:
    author = author_service.update_author(author_id, body)
    if not author:
        abort(HTTPStatus.NOT_FOUND)
    return author
