from fastopenapi.error_handler import ResourceNotFoundError
from fastopenapi.routers import DjangoRouter

from ...schemas.authors import (
    AuthorSchema,
    CreateAuthorSchema,
    FilterAuthorSchema,
    UpdateAuthorSchema,
)
from ...services.authors import AuthorService

author_service = AuthorService()

router = DjangoRouter()


@router.post(
    "/authors",
    tags=["Authors"],
    status_code=201,
    response_errors=[400, 422, 500],
    response_model=AuthorSchema,
)
def create_author(body: CreateAuthorSchema) -> AuthorSchema:
    return author_service.create_author(body)


@router.get(
    "/authors/{author_id}",
    tags=["Authors"],
    response_errors=[400, 404, 500],
    response_model=AuthorSchema,
)
def get_author(author_id: int) -> AuthorSchema:
    author = author_service.get_author(author_id)
    if not author:
        raise ResourceNotFoundError("Author not found")
    return author


@router.get(
    "/authors/",
    tags=["Authors"],
    response_errors=[500],
    response_model=list[AuthorSchema],
)
def get_authors(body: FilterAuthorSchema) -> list[AuthorSchema]:
    return author_service.get_authors(body)


@router.delete(
    "/authors/{author_id}",
    tags=["Authors"],
    status_code=204,
    response_errors=[400, 404, 500],
)
def delete_author(author_id: int) -> None:
    author = author_service.delete_author(author_id)
    if not author:
        raise ResourceNotFoundError("Author not found")


@router.patch(
    "/authors/{author_id}",
    tags=["Authors"],
    response_errors=[400, 404, 422, 500],
    response_model=AuthorSchema,
)
def update_author(author_id: int, body: UpdateAuthorSchema) -> AuthorSchema:
    author = author_service.update_author(author_id, body)
    if not author:
        raise ResourceNotFoundError("Author not found")
    return author
