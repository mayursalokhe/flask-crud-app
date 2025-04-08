from pydantic import BaseModel, Field
from typing import Optional, List

class CreateItemRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=3)
    price: float = Field(..., ge=0)

class UpdateItemRequest(BaseModel):
    name: str = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=3)
    price: float = Field(None, ge=0)

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    created_at: str  # ISO 8601 Date String (e.g., '2023-10-07T13:45:00')

class GetAllItems(BaseModel):
    items: List[ItemResponse]

