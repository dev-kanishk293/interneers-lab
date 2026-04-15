from pydantic import BaseModel, Field
from typing import List, Optional

class ProductValidator(BaseModel):
    name: str = Field(..., max_length=255)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., max_length=255)
    price: float = Field(..., ge=0)
    brand: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(..., ge=0)
    category_ids: List[int] = Field(default_factory=list)

class ProductListValidator(BaseModel):
    products: List[ProductValidator]
