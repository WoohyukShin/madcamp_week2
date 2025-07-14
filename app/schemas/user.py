from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    imageURL: Optional[str] = None
    nickname: str
    birthday: Optional[datetime] = None
    gender: Optional[str] = None
