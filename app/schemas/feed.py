from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, EmailStr

class FeedImageResponse(BaseModel):
    id: int
    imageURL: str

class CommentResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    content: str
    created_at: datetime
    likes: int
    user_likes: bool
    updated_at: datetime
    replies: List[CommentResponse] = []

class FeedResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    content: str
    created_at: datetime 
    likes: int
    saves: int
    user_likes: bool
    user_saves: bool
    images: List[FeedImageResponse]
    comments: List[CommentResponse]

class CommentCreateRequest(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentEditRequest(BaseModel):
    content: str