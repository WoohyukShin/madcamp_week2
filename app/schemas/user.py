from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    imageURL: Optional[str] = None
    nickname: str
    birthday: datetime
    gender: str
