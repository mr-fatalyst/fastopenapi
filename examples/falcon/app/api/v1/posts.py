import falcon

from fastopenapi.routers import FalconRouter

from ...schemas.posts import (
    CreatePostSchema,
    FilterPostSchema,
    PostSchema,
    UpdatePostSchema,
)
from ...services.posts import PostService

post_service = PostService()
router = FalconRouter()


@router.post(
    "/posts",
    tags=["Posts"],
    status_code=201,
    response_errors=[400, 422, 500],
    response_model=PostSchema,
)
async def create_post(body: CreatePostSchema) -> PostSchema:
    return await post_service.create_post(body)


@router.get(
    "/posts/{post_id}",
    tags=["Posts"],
    response_errors=[400, 404, 500],
    response_model=PostSchema,
)
async def get_post(post_id: int) -> PostSchema:
    post = await post_service.get_post(post_id)
    if not post:
        raise falcon.HTTPNotFound()
    return post


@router.get(
    "/posts/", tags=["Posts"], response_errors=[500], response_model=list[PostSchema]
)
async def get_posts(body: FilterPostSchema) -> list[PostSchema]:
    return await post_service.get_posts(body)


@router.delete(
    "/posts/{post_id}", tags=["Posts"], status_code=204, response_errors=[400, 404, 500]
)
async def delete_post(post_id: int) -> None:
    post = await post_service.delete_post(post_id)
    if not post:
        raise falcon.HTTPNotFound()


@router.patch(
    "/posts/{post_id}",
    tags=["Posts"],
    response_errors=[400, 404, 422, 500],
    response_model=PostSchema,
)
async def update_post(post_id: int, body: UpdatePostSchema) -> PostSchema:
    post = await post_service.update_post(post_id, body)
    if not post:
        raise falcon.HTTPNotFound()
    return post
