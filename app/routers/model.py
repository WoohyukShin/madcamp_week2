import os
import redis
import requests
import numpy as np
from typing import Optional, Dict
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.product import build_product_summary_response

router = APIRouter(prefix="/model")
r = redis.Redis.from_url(os.getenv("REDIS_URL"))

threshold_text = 0.15
threshold_image = 0.2

@router.post("/set_colab_url")
async def set_colab_url(req: Request, db: Session = Depends(get_db)):
    data = await req.json()
    colab_url = data.get("colab_url")
    r.set("COLAB_SERVER_URL", colab_url)
    print(f"new COLAB_SERVER_URL={colab_url}")

    products = db.query(Product).filter(Product.embedding != None).all()
    
    product_vectors = []
    for p in products:
        product_vectors.append({
            "id": p.id,
            "embedding": p.embedding,
            "label": p.category
        })

    try:
        import requests
        response = requests.post(
            f"{colab_url}/init/embeddings",
            json={"products": product_vectors}
        )
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send embeddings to Colab: {e}")

    return {"message": "colab_url and product embeddings initialized"}

@router.post("/recommend/text", response_model=Dict[str, List[ProductSummaryResponse]])
def get_recommendation_from_text(
    text: str = Form(...),
    r: int = Form(...),
    g: int = Form(...),
    b: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")

    image.file.seek(0)
    files = {
        "image": (image.filename, image.file, image.content_type)
    }
    data = {
        "text": text,
        "r": r,
        "g": g,
        "b": b
    }

    try:
        response = requests.post(f"{colab_url}/recommend/text", files=files, data=data)
        response.raise_for_status()
        result = response.json()  # { "label1": [1,2,3], "label2": [4,5] }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendation from Colab: {e}")

    recommendations = {}
    for label, id_list in result.items():
        products = db.query(Product).filter(Product.id.in_(id_list)).all()
        recommendations[label] = [
            build_product_summary_response(p, user.id) for p in products
        ]
    return recommendations

@router.post("/recommend/image", response_model=Dict[str, List[ProductSummaryResponse]])
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

    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")

    if image:
        import json
        image.file.seek(0)
        files = {
            "image": (image.filename, image.file, image.content_type)
        }
        data = {
            "embedding": json.dumps(wish_embedding)
        }

        try:
            response = requests.post(f"{colab_url}/recommend/image", files=files, data=data)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch recommendation from Colab: {e}")

    recommendations = {}
    for label, id_list in result.items():
        products = db.query(Product).filter(Product.id.in_(id_list)).all()
        recommendations[label] = [
            build_product_summary_response(p, user.id) for p in products
        ]

    return recommendations

