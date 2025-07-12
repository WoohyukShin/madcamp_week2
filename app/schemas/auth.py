from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    nickname: str
    password: str
    birthday: Optional[datetime] = None
    gender: Optional[str] = None
    code: Optional[str] = None # naver 등 연동 시 코드
    auth_type: Optional[str] = None # "naver", "kakao", "facebook"

class VertifyRequest(BaseModel):
    email: EmailStr
    code: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class OAuthLoginRequest(BaseModel):
    code: str
    auth_type: Literal["naver", "kakao", "facebook"]

class LoginResponse(BaseModel):
    success: bool

    access_token: str
    token_type: str

class OAuthLoginResponse(BaseModel):
    exists: bool 

    access_token: Optional[str] = None # if user exists
    token_type: Optional[str] = None

    email: Optional[EmailStr] = None # if user NOT exists
    name: Optional[str] = None

class SignupResponse(BaseModel):
    message: str
    user_id: int

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    new_password: str
    new_password_check: str

class PasswordResetCodeRequest(BaseModel):
    email: EmailStr
    code: str

