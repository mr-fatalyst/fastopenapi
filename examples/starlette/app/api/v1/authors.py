from starlette.exceptions import HTTPException

from fastopenapi.routers import StarletteRouter

from ...schemas.authors import (
    AuthorSchema,
    CreateAuthorSchema,
    FilterAuthorSchema,
    UpdateAuthorSchema,
)
from ...services.authors import AuthorService

author_service = AuthorService()

router = StarletteRouter()


@router.post("/authors", tags=["Authors"], status_code=201, response_model=AuthorSchema)
async def create_author(body: CreateAuthorSchema) -> AuthorSchema:
    return await author_service.create_author(body)


@router.get("/authors/{author_id}", tags=["Authors"], response_model=AuthorSchema)
async def get_author(author_id: int) -> AuthorSchema:
    author = await author_service.get_author(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Not Found")
    return author


@router.get("/authors/", tags=["Authors"], response_model=list[AuthorSchema])
async def get_authors(body: FilterAuthorSchema) -> list[AuthorSchema]:
    return await author_service.get_authors(body)


@router.delete("/authors/{author_id}", tags=["Authors"], status_code=204)
async def delete_author(author_id: int) -> None:
    author = await author_service.delete_author(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Not Found")


@router.patch("/authors/{author_id}", tags=["Authors"], response_model=AuthorSchema)
async def update_author(author_id: int, body: UpdateAuthorSchema) -> AuthorSchema:
    author = await author_service.update_author(author_id, body)
    if not author:
        raise HTTPException(status_code=404, detail="Not Found")
    return author
