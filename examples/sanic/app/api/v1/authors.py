from sanic import NotFound

from fastopenapi.routers import SanicRouter

from ...schemas.authors import (
    AuthorSchema,
    CreateAuthorSchema,
    FilterAuthorSchema,
    UpdateAuthorSchema,
)
from ...services.authors import AuthorService

author_service = AuthorService()

router = SanicRouter()


@router.post(
    "/authors",
    tags=["Authors"],
    status_code=201,
    response_errors=[400, 422, 500],
    response_model=AuthorSchema,
)
async def create_author(body: CreateAuthorSchema) -> AuthorSchema:
    return await author_service.create_author(body)


@router.get(
    "/authors/{author_id}",
    tags=["Authors"],
    response_errors=[400, 404, 500],
    response_model=AuthorSchema,
)
async def get_author(author_id: int) -> AuthorSchema:
    author = await author_service.get_author(author_id)
    if not author:
        raise NotFound()
    return author


@router.get(
    "/authors/",
    tags=["Authors"],
    response_errors=[500],
    response_model=list[AuthorSchema],
)
async def get_authors(body: FilterAuthorSchema) -> list[AuthorSchema]:
    return await author_service.get_authors(body)


@router.delete(
    "/authors/{author_id}",
    tags=["Authors"],
    status_code=204,
    response_errors=[400, 404, 500],
)
async def delete_author(author_id: int) -> None:
    author = await author_service.delete_author(author_id)
    if not author:
        raise NotFound()


@router.patch(
    "/authors/{author_id}",
    tags=["Authors"],
    response_errors=[400, 404, 422, 500],
    response_model=AuthorSchema,
)
async def update_author(author_id: int, body: UpdateAuthorSchema) -> AuthorSchema:
    author = await author_service.update_author(author_id, body)
    if not author:
        raise NotFound()
    return author
