from pydantic import BaseModel, Field


class AuthorSchema(BaseModel):
    id: int
    name: str
    bio: str | None = None


class FilterAuthorSchema(BaseModel):
    id: int = Field(default=None)
    name: str = Field(default=None)


class CreateAuthorSchema(BaseModel):
    name: str = Field(..., max_length=50)
    bio: str | None = Field(None, max_length=200)


class UpdateAuthorSchema(BaseModel):
    name: str = Field(default=None, max_length=50)
    bio: str = Field(default=None, max_length=200)
