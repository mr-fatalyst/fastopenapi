import falcon

from ..schemas.posts import (
    CreatePostSchema,
    FilterPostSchema,
    PostSchema,
    UpdatePostSchema,
)
from ..storage import authors, posts


class PostService:
    async def create_post(self, body: CreatePostSchema) -> PostSchema:
        post_counter = len(posts)
        author = authors.get(body.author_id)
        if not author:
            raise falcon.HTTPNotFound(description="Author not found")

        data = {
            "id": post_counter,
            "title": body.title,
            "content": body.content,
            "author_id": body.author_id,
        }
        post = PostSchema(**data)
        posts[post_counter] = post
        return post

    async def get_post(self, post_id: int) -> PostSchema | None:
        return posts.get(post_id)

    async def get_posts(self, body: FilterPostSchema) -> list[PostSchema]:
        def match(post: PostSchema) -> bool:
            for field, value in body.model_dump(exclude_none=True).items():
                if getattr(post, field) != value:
                    return False
            return True

        return [item for _, item in posts.items() if match(item)]

    async def update_post(
        self, post_id: int, body: UpdatePostSchema
    ) -> PostSchema | None:
        post = posts.get(post_id)
        if post:
            updated_post = post.copy(update=body.model_dump(exclude_unset=True))
            posts[post_id] = updated_post
            return updated_post
        return None

    async def delete_post(self, post_id: int) -> int | None:
        return posts.pop(post_id, None)
