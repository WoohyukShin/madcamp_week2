import os
import redis
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from app.utils.model import get_image_embedding, get_text_embedding
from sqlalchemy.orm import Session
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user

router = APIRouter(prefix="/model")
r = redis.Redis.from_url(os.getenv("REDIS_URL"))

@router.post("/set_colab_url")
async def set_colab_url(req: Request): # Colab 로컬 서버 다시 열릴 때마다 url 입력받아서 저장
    data = await req.json()
    colab_url = data.get("colab_url")
    r.set("COLAB_SERVER_URL", colab_url)
    print(f"new COLAB_SERVER_URL={colab_url}")
    return {"message": "colab_url saved"}
'''
@router.get("/recommend/text") # style text랑, color RGB 값 0-256 int(?)로 받음
def get_recommendation_from_text(text: str = Form(...), image: UploadFile = File(),
                                db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    
    image_embedding = get_image_embedding(image)
    bad_objects = get_bad_objects_with_text(image, image_embedding)
    for objects in bad_objects:

        # 일단 나중에~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!
    return None

@router.get("/recommend/image")
def get_recommendation_from_image(image_id: int, image: UploadFile = File(),
                                db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    wish_image: FeedImage = db.query(FeedImage).filter(FeedImage.id == image_id).first()
    wish_embedding = wish_image.embedding.embedding
    image_embedding = get_image_embedding(image)

    bad_objects = get_bad_objects_with_image(image, image_embedding)
    for object in bad_objects:


    return None
'''