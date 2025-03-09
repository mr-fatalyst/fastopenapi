from ..schemas.authors import (
    AuthorSchema,
    CreateAuthorSchema,
    FilterAuthorSchema,
    UpdateAuthorSchema,
)
from ..storage import authors, posts


class AuthorService:
    async def create_author(self, body: CreateAuthorSchema) -> AuthorSchema:
        author_counter = len(authors)
        data = {"id": author_counter, "name": body.name, "bio": body.bio}
        author = AuthorSchema(**data)
        authors[author_counter] = author
        return author

    async def get_author(self, author_id: int) -> AuthorSchema | None:
        return authors.get(author_id)

    async def get_authors(self, body: FilterAuthorSchema) -> list[AuthorSchema]:
        def match(author: AuthorSchema) -> bool:
            for field, value in body.model_dump(exclude_none=True).items():
                if getattr(author, field) != value:
                    return False
            return True

        return [item for _, item in authors.items() if match(item)]

    async def update_author(
        self, author_id: int, body: UpdateAuthorSchema
    ) -> AuthorSchema | None:
        author = authors.get(author_id)
        if author:
            updated_author = author.copy(update=body.model_dump(exclude_unset=True))
            authors[author_id] = updated_author
            return updated_author
        return None

    async def delete_author(self, author_id: int) -> int | None:
        author_id = authors.pop(author_id, None)
        if author_id:
            keys_to_remove = [
                post_id
                for post_id, post in posts.items()
                if post["author_id"] == author_id
            ]
            for key in keys_to_remove:
                del posts[key]
        return author_id
