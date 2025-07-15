from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, EmailStr

class RecommendRequest(BaseModel):
    text: Optional[str] = None
    image_id: Optional[int] = None

class ProductVector(BaseModel):
    id: int
    embedding: List[float]
    label: str