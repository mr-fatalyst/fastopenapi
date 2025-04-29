from pydantic import BaseModel, Field


class PostSchema(BaseModel):
    id: int
    title: str
    content: str
    author_id: int


class FilterPostSchema(BaseModel):
    id: int = Field(default=None)
    title: str = Field(default=None)


class CreatePostSchema(BaseModel):
    title: str = Field(..., max_length=100)
    content: str
    author_id: int


class UpdatePostSchema(BaseModel):
    title: str = Field(default=None, max_length=100)
    content: str = Field(default=None)
