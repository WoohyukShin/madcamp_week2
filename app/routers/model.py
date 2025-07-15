import os
import redis
import numpy as np
from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from app.utils.model import get_text_embedding, get_text_embedding_with_rgb, analyze_bad_objects_with_image, analyze_bad_objects_with_text
from sqlalchemy.orm import Session
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user

router = APIRouter(prefix="/model")
r = redis.Redis.from_url(os.getenv("REDIS_URL"))

threshold_text = 0.15
threshold_image = 0.2

@router.post("/set_colab_url")
async def set_colab_url(req: Request): # Colab 로컬 서버 다시 열릴 때마다 url 입력받아서 저장
    data = await req.json()
    colab_url = data.get("colab_url")
    r.set("COLAB_SERVER_URL", colab_url)
    print(f"new COLAB_SERVER_URL={colab_url}")
    return {"message": "colab_url saved"}

@router.post("/recommend/text") # style text랑, color RGB 값 0-256 int로 받아서 { "의자":List[ProductResponse...], "기타": List.... }
def get_recommendation_from_text(text: str=Form(...), r:int=Form(...), g:int=Form(...), b:int=Form(...), image: UploadFile = File(),
                                db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    
    return None

@router.post("/recommend/image", response_model=dict)
def get_recommendation_from_image(
    image_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return None