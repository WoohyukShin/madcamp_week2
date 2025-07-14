import os
import json
import redis
import requests
import smtplib
import random, string

from dotenv import load_dotenv
from app.models.user import User
from email.mime.text import MIMEText
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.db.db import get_db
from fastapi.security import OAuth2PasswordBearer



load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

r = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)

def verify_email(email: str):
    verification_code = generate_code()

    data = {"code": verification_code}
    r.setex(f"verify:{email}", 600, json.dumps(data))
    send_verification_email(email, verification_code)

    return {"message": "Verification code sent"}

def generate_code(length: int = 6) -> str: # 메일 인증 코드 생성 (숫자 6자리 string)
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email: str, verification_code: str):
    try:
        sender = os.getenv("GMAIL_USER")
        password = os.getenv("GMAIL_PASSWORD")

        if not sender or not password:
            raise RuntimeError("Gmail credentials not found in environment variables")

        msg = MIMEText(f"안녕하세요? 강도입니다.\n귀하의 소중한 개인 정보가 노출되었습니다.\n복구를 위한 인증 코드는 다음과 같습니다 : {verification_code}")
        msg["Subject"] = "[국제발신] 귀하의 개인 정보가 노출되었습니다."
        msg["From"] = sender
        msg["To"] = email

        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(sender, password)
        smtp.sendmail(sender, [email], msg.as_string())
        smtp.quit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

SECRET_KEY = "asdfasdfasdf"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365 * 10

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

'''
def get_user_info_from_kakao(code: str):
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("KAKAO_CLIENT_ID"),
        "redirect_uri": os.getenv("KAKAO_REDIRECT_URI"),
        "code": code,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    token_response = requests.post(token_url, data=token_data, headers=token_headers)

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패")

    access_token = token_response.json().get("access_token")

    user_info_url = "https://kapi.kakao.com/v2/user/me"
    user_info_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    user_response = requests.get(user_info_url, headers=user_info_headers)

    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")

    id  = user_response.json().get("id")
    email = f"{id}@kakao.com"
    return {
        "email": email,
        "name": "",
    }
'''

'''
def get_user_info_from_naver(code: str, state: str = "안녕하세용?"):
    token_url = "https://nid.naver.com/oauth2.0/token"
    token_params = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("NAVER_CLIENT_ID"),
        "client_secret": os.getenv("NAVER_CLIENT_SECRET"),
        "code": code,
        "state": state,
    }

    token_response = requests.get(token_url, params=token_params)
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="네이버 토큰 발급 실패")

    access_token = token_response.json().get("access_token")

    user_info_url = "https://openapi.naver.com/v1/nid/me"
    user_info_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_response = requests.get(user_info_url, headers=user_info_headers)
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="네이버 사용자 정보 조회 실패")

    response_data = user_response.json().get("response", {})

    email = response_data.get("email")
    name = response_data.get("name")
    return {
        "email": email,
        "name": name,
    }
'''

def get_user_info_from_facebook(code: str):
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    token_params = {
        "client_id": os.getenv("FACEBOOK_CLIENT_ID"),
        "redirect_uri": os.getenv("FACEBOOK_REDIRECT_URI"),
        "client_secret": os.getenv("FACEBOOK_CLIENT_SECRET"),
        "code": code,
    }

    token_response = requests.get(token_url, params=token_params)
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Facebook 토큰 발급 실패")

    access_token = token_response.json().get("access_token")

    user_info_url = "https://graph.facebook.com/me"
    user_info_params = {
        "fields": "id,name,email,picture,birthday,gender",
        "access_token": access_token,
    }

    user_response = requests.get(user_info_url, params=user_info_params)
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Facebook 사용자 정보 조회 실패")
    
    user_data = user_response.json()
    
    email = user_data.get("email")
    name = user_data.get("name")

    return {
        "email": email,
        "name": name,
    }

