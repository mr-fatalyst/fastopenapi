from pydantic import BaseModel, Field


class RecordCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_completed: bool = Field(False)


class RecordUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_completed: bool | None = None


class RecordResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    is_completed: bool
