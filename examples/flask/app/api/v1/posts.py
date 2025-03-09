from http import HTTPStatus

from flask import abort

from fastopenapi.routers.flask import FlaskRouter

from ...schemas.posts import (
    CreatePostSchema,
    FilterPostSchema,
    PostSchema,
    UpdatePostSchema,
)
from ...services.posts import PostService

post_service = PostService()
router = FlaskRouter()


@router.post("/posts", tags=["Posts"], status_code=201, response_model=PostSchema)
def create_post(body: CreatePostSchema) -> PostSchema:
    return post_service.create_post(body)


@router.get("/posts/{post_id}", tags=["Posts"], response_model=PostSchema)
def get_post(post_id: int) -> PostSchema:
    post = post_service.get_post(post_id)
    if not post:
        abort(HTTPStatus.NOT_FOUND)
    return post


@router.get("/posts/", tags=["Posts"], response_model=list[PostSchema])
def get_posts(body: FilterPostSchema) -> list[PostSchema]:
    return post_service.get_posts(body)


@router.delete("/posts/{post_id}", tags=["Posts"], status_code=204)
def delete_post(post_id: int) -> None:
    post = post_service.delete_post(post_id)
    if not post:
        abort(HTTPStatus.NOT_FOUND)


@router.patch("/posts/{post_id}", tags=["Posts"], response_model=PostSchema)
def update_post(post_id: int, body: UpdatePostSchema) -> PostSchema:
    post = post_service.update_post(post_id, body)
    if not post:
        abort(HTTPStatus.NOT_FOUND)
    return post
