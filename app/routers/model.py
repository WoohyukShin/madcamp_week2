import os
import redis
import numpy as np
from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from app.utils.model import get_text_embedding, get_text_embedding_with_rgb, analyze_bad_objects_with_image, analyze_bad_objects_with_text
from sqlalchemy.orm import Session, func
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from pgvector.sqlalchemy import cosine_similarity

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
    
    style_embedding, color = get_text_embedding_with_rgb(text, r, g, b) # "scandinavian", int, int, int -> 
    prompt = f"{color} colored {text} style "
    bad_objects = analyze_bad_objects_with_text(image=image, prompt=prompt)

    recommendations = {}
    used_ids = set()

    for label in bad_objects:
        prompt = f"{color} colored {text} style {label}"
        prompt_embedding = get_text_embedding(prompt)

        top_k_products = (
            db.query(Product)
            .filter(Product.embedding != None)
            .order_by(func.cosine_distance(Product.embedding, prompt_embedding))
            .limit(6)
            .all()
        )

        used_ids.update(p.id for p in top_k_products)
        recommendations[label] = [
            ProductResponse(**p.__dict__, user_saves=False) for p in top_k_products
        ]

    top_k_etc = (
        db.query(Product)
        .filter(Product.embedding != None, ~Product.id.in_(used_ids))
        .order_by(func.cosine_distance(Product.embedding, style_embedding))
        .limit(30) 
        .all()
    )

    top_k_filtered = []
    for p in top_k_etc:
        sim = cosine_similarity(
            np.array([style_embedding]),
            np.array([p.embedding])
        )[0][0]
        if sim > threshold_text:
            top_k_filtered.append(p)
        if len(top_k_filtered) >= 10:
            break

    recommendations["기타"] = [
        ProductResponse(**p.__dict__, user_saves=False) for p in top_k_filtered
    ]

    return recommendations

@router.post("/recommend/image", response_model=dict)
def get_recommendation_from_image(
    image_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    feed_image = db.query(FeedImage).filter(FeedImage.id == image_id).first()
    if not feed_image or feed_image.embedding is None:
        raise HTTPException(status_code=404, detail="Not Found")

    wish_embedding = feed_image.embedding

    if image:
        bad_objects = analyze_bad_objects_with_image(image=image, embedding=wish_embedding)
    else:
        bad_objects = []

    recommendations = {}
    used_ids = set()

    for label in bad_objects:
        top_k_products = (
            db.query(Product)
            .filter(Product.embedding != None)
            .order_by(func.cosine_distance(Product.embedding, wish_embedding))
            .limit(6)
            .all()
        )
        used_ids.update(p.id for p in top_k_products)
        recommendations[label] = [
            ProductResponse(**p.__dict__, user_saves=False) for p in top_k_products
        ]

    top_k_etc = (
        db.query(Product)
        .filter(Product.embedding != None, ~Product.id.in_(used_ids))
        .order_by(func.cosine_distance(Product.embedding, wish_embedding))
        .limit(30)
        .all()
    )

    top_k_filtered = []
    for p in top_k_etc:
        sim = cosine_similarity(
            np.array([wish_embedding]),
            np.array([p.embedding])
        )[0][0]
        if sim > threshold_image:
            top_k_filtered.append(p)
        if len(top_k_filtered) >= 6:
            break
    recommendations["기타"] = [
        ProductResponse(**p.__dict__, user_saves=False) for p in top_k_filtered
    ]
    return recommendations