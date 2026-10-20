import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Therapeutic category name")
    description: Optional[str] = Field(None, max_length=500, description="Clinical or therapeutic description")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    medicine_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
