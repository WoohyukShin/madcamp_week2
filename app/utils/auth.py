import os
import redis
import random, string

from app.models.user import User
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.db.db import get_db
from fastapi.security import OAuth2PasswordBearer
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def generate_code(length: int = 6) -> str: # 메일 인증 코드 생성 (숫자 6자리 string)
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email: str, vertification_code: str): # email로 vertification code 보냄
    message = Mail(
        from_email="urihiya1@kaist.ac.kr",
        to_emails=email,
        subject="Your Verification Code",
        plain_text_content=f"Your verification code is: {vertification_code}"
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        sg.send(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send email")

SECRET_KEY = "asdfasdfasdf"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_jwt_token(user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": str(user_id), "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except JWTError:
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
        
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = decode_jwt_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Inactive or non-existent user")

    return user
