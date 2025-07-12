import os
import json
import redis
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db.db import get_db
from app.models.user import User
from app.schemas import *
from app.utils.auth import generate_code, send_verification_email, get_password_hash, verify_password, create_jwt_token, get_current_user, get_user_info_from_facebook, get_user_info_from_kakao, get_user_info_from_naver

load_dotenv()

r = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)
router = APIRouter(prefix="/auth")

@router.get("/check-nickname") # 중복확인 눌렀을 때 닉네임 중복 체크
def check_nickname(nickname: str = Query(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.nickname == nickname).first():
        return {"available": False}
    return {"available": True}

@router.post("/signup") # 이메일, 이름, nickname... 등 기본적인 signup request를 받아서 인증 메일 보내고 알려줌.
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="email already exists")
    if db.query(User).filter(User.nickname == user_data.nickname).first():
        raise HTTPException(status_code=400, detail="nickname already exists")
    
    vertification_code = generate_code()
    redis_value = user_data.model_dump()
    redis_value["code"] = vertification_code
    r.setex(f"verify:{user_data.email}", 600, json.dumps(redis_value))
    send_verification_email(user_data.email, vertification_code)
    return { "message" : "Vertification code sent" }
    
@router.post("/vertify") # 인증 코드 받아서 확인되면 아까 입력된 정보로 User 만들고 new User의 id 반환
def vertify_email(request: VertifyRequest, db: Session = Depends(get_db)):
    code = request.code
    email = request.email
    value = r.get(f"verify:{email}")
    if not value:
        raise HTTPException(status_code=400, detail="Signup info expired or not found")
    
    user_data = json.loads(value)
    if user_data["code"] != code:
        raise HTTPException(status_code=400, detail="Wrong vertification code")
    
    new_user = User(
        email=user_data["email"],
        name=user_data["name"],
        imageURL=None,
        nickname=user_data["nickname"],
        password=get_password_hash(user_data["password"]),
        birthday=user_data["birthday"],
        gender=user_data["gender"],
        auth_type="email"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    r.delete(f"verify:{email}")
    return SignupResponse("회원가입 성공", new_user.id)

@router.post("/login", response_model=LoginResponse) # 그냥 메일로 로그인, token 반환
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")

    token = create_jwt_token(user.id)
    return LoginResponse(success = True, access_token=token, token_type="bearer")

@router.post("/signup/oauth") # oauth login fail -> 회원가입 창에서 new signup request를 받았을 때
def oauth_signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    if user_data.auth_type not in {"naver", "kakao", "facebook"}:
        raise HTTPException(status_code=400, detail="Unsupported auth_type")

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="email already exists")
    if db.query(User).filter(User.nickname == user_data.nickname).first():
        raise HTTPException(status_code=400, detail="nickname already exists")
    
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        imageURL=None,
        nickname=user_data.nickname,
        password=None,
        birthday=user_data.birthday,
        gender=user_data.gender,
        auth_type=user_data.auth_type
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return SignupResponse("회원가입 성공", new_user.id)

@router.post("/login/oauth") # oauth 연동해서 로그인, 성공 여부와 함께 마찬가지로 token 반환 (false면 front에서 oauth 기반 회원가입 창으로 넘어감)
def oauth_login(request: OAuthLoginRequest, db: Session = Depends(get_db)):
    code = request.code
    auth_type = request.auth_type
    if auth_type == "naver":
        user_info = get_user_info_from_naver(code)
    elif auth_type == "kakao":
        user_info = get_user_info_from_kakao(code)
    elif auth_type == "facebook":
        user_info = get_user_info_from_facebook(code)
    else:
        raise HTTPException(status_code=400, detail="Unsupported auth_type")

    email = user_info["email"]
    name = user_info["name"]
    user: User = db.query(User).filter(User.email == email).first()
    if not user:
        return OAuthLoginResponse(False, email = email, name = name)
    
    token = create_jwt_token(user.id)
    return OAuthLoginResponse(True, token = token, token_type = "bearer")

@router.post("/lost-password") # 비번 잃어버려서 메일을 받은 다음, 메일로 인증 코드 보내고 알려줌
def lost_password(email: str = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    vertification_code = generate_code()
    r.setex(f"reset:{email}", 600, vertification_code)

    send_verification_email(email, vertification_code)
    return {"message": "Reset code sent"}

@router.post("/vertify-reset-code") # 비번 잃어버린 뒤 인증 코드 받고, 인증해 준 뒤 결과 반환
def verify_reset_code(request: PasswordResetCodeRequest):
    stored_code = r.get(f"reset:{request.email}")
    if not stored_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    if stored_code != request.code:
        raise HTTPException(status_code=400, detail="Wrong vertification code")
    
    r.delete(f"reset:{request.email}")
    return {"message": "Code verified"}

@router.post("/reset-password") # 새 비번, 새 비번 확인 받아서 변경해 줌
def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if request.new_password != request.new_password_check:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    current_user.password = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password reset successful"}

# 혹시니 비밀번호 변경이 생기게 된다면 ... 일단 만들어놓긴 해서 @router.get("change-password")
'''
@router.post("/change-password")
def change_password(request: PasswordChangeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if not verify_password(request.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    current_user.password = get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}
'''

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
