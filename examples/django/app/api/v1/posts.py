from fastopenapi.error_handler import ResourceNotFoundError
from fastopenapi.routers import DjangoRouter

from ...schemas.posts import (
    CreatePostSchema,
    FilterPostSchema,
    PostSchema,
    UpdatePostSchema,
)
from ...services.posts import PostService

post_service = PostService()
router = DjangoRouter()


@router.post(
    "/posts",
    tags=["Posts"],
    status_code=201,
    response_errors=[400, 422, 500],
    response_model=PostSchema,
)
def create_post(body: CreatePostSchema) -> PostSchema:
    return post_service.create_post(body)


@router.get(
    "/posts/{post_id}",
    tags=["Posts"],
    response_errors=[400, 404, 500],
    response_model=PostSchema,
)
def get_post(post_id: int) -> PostSchema:
    post = post_service.get_post(post_id)
    if not post:
        raise ResourceNotFoundError("Author not found")
    return post


@router.get(
    "/posts/", tags=["Posts"], response_errors=[500], response_model=list[PostSchema]
)
def get_posts(body: FilterPostSchema) -> list[PostSchema]:
    return post_service.get_posts(body)


@router.delete(
    "/posts/{post_id}", tags=["Posts"], status_code=204, response_errors=[400, 404, 500]
)
def delete_post(post_id: int) -> None:
    post = post_service.delete_post(post_id)
    if not post:
        raise ResourceNotFoundError("Post not found")


@router.patch(
    "/posts/{post_id}",
    tags=["Posts"],
    response_errors=[400, 404, 422, 500],
    response_model=PostSchema,
)
def update_post(post_id: int, body: UpdatePostSchema) -> PostSchema:
    post = post_service.update_post(post_id, body)
    if not post:
        raise ResourceNotFoundError("Post not found")
    return post
