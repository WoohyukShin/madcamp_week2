import os
import redis
import requests
from app.schemas import *
from typing import List
from datetime import datetime
from fastapi import APIRouter, Form, File, UploadFile, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.models import *
from app.db.db import get_db
from app.utils.auth import get_current_user
from app.utils.image import save_image, delete_image
from app.utils.model import get_image_embedding

router = APIRouter(prefix="/product")
r = redis.Redis.from_url(os.getenv("REDIS_URL"))


@router.get("/products", response_model=List[ProductResponse])  # 상품 목록 조회 (내가 save한 상품 제외)
def get_products(page: int = Query(..., ge=1), limit: int = Query(...),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    saved_product_ids = db.query(ProductSave.product_id).filter(ProductSave.user_id == user.id)
    products: List[Product]=(db.query(Product).filter(Product.id.not_in(saved_product_ids))
                             .order_by(Product.created_at.desc()).offset(offset).limit(limit).all())
    
    response = []
    for product in products:
        response.append(ProductResponse(
            id=product.id,
            user_id=product.user_id,
            name=product.name,
            content=product.content,
            price=product.price,
            imageURL=product.imageURL,
            created_at=product.created_at,
            is_sold=product.is_sold,
            saves=product.saves,
            user_saves=False
        ))
    return response

@router.post("")  # 상품 추가
def create_product(name: str = Form(...), content: str = Form(...), price: int = Form(...),
    image: UploadFile = File(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):

    imageURL = save_image(image, "products")
    embedding = get_image_embedding(image)

    product = Product(
        user_id=user.id,
        name=name,
        content=content,
        price=price,
        imageURL=imageURL,
        embedding=embedding
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return {"message": "상품 등록 완료", "product_id": product.id}

@router.put("/{product_id}")  # 상품 수정
def update_product(
    product_id: int,
    name: str = Form(...),
    content: str = Form(...),
    price: int = Form(...),
    new_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = name
    product.content = content
    product.price = price

    if new_image:
        if product.imageURL:
            delete_image(product.imageURL, "products")

        image_url = save_image(new_image, "products")
        product.imageURL = image_url
        embedding = get_image_embedding(new_image)
        product.embedding = embedding

    db.commit()
    return {"message": "상품 수정 완료"}

@router.delete("/{product_id}")  # 상품 삭제
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.imageURL:
        delete_image(product.imageURL, "products")

    db.delete(product)
    db.commit()
    return {"message": "상품 삭제 완료"}

@router.get("/products/me", response_model=List[ProductResponse])  # 내 상품 목록
def get_my_products(page: int=Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    products: List[Product] = (db.query(Product).filter(Product.user_id == user.id).order_by(Product.created_at.desc()).offset(offset).limit(limit).all())

    response = []
    for product in products:
        response.append(ProductResponse(
            id=product.id,
            user_id=product.user_id,
            name=product.name,
            content=product.content,
            price=product.price,
            imageURL=product.imageURL,
            created_at=product.created_at,
            is_sold=product.is_sold,
            saves=product.saves,
            user_saves=False
        ))

    return response

@router.get("/products/saved") # 장바구니에 추가한 상품 목록
def get_saved_products(page: int=Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    saved_product_ids = (db.query(ProductSave.product_id).filter(ProductSave.user_id == user.id).subquery())

    products: List[Product] = (db.query(Product).filter(Product.id.in_(saved_product_ids)).order_by(Product.created_at.desc())
        .offset(offset).limit(limit).all())

    response = []
    for product in products:
        response.append(ProductResponse(
            id=product.id,
            user_id=product.user_id,
            name=product.name,
            content=product.content,
            price=product.price,
            imageURL=product.imageURL,
            created_at=product.created_at,
            is_sold=product.is_sold,
            saves=product.saves,
            user_saves=True
        ))

    return response

@router.post("/{product_id}/save")  # 장바구니에 추가
def save_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    already_saved = db.query(ProductSave).filter(
        ProductSave.product_id == product_id,
        ProductSave.user_id == user.id
    ).first()

    if already_saved:
        db.delete(already_saved)
        product.saves -= 1
        action = "unsaved"
    else:
        save = ProductSave(user_id=user.id, product_id=product_id, created_at=datetime.utcnow())
        db.add(save)
        product.saves += 1
        action = "saved"

    db.commit()
    return {"is_saved": action == "saved", "saves": product.saves} 


