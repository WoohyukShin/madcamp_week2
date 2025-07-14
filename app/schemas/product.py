from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductResponse(BaseModel):
    id: int
    user_id: int
    name: str
    content: str
    price: int
    imageURL: str
    created_at: datetime
    is_sold: bool
    saves: int
    user_saves: bool