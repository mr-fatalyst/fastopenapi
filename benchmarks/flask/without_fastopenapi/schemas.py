from pydantic import BaseModel, Field, field_validator


class RecordCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_completed: bool = Field(False)

    @field_validator("title")
    @classmethod
    def title_cannot_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v


class RecordUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_cannot_be_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v


class RecordResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    is_completed: bool
