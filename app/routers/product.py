import os
import json
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
from app.utils.product import build_product_response, build_product_summary_response, build_product_saved_response

router = APIRouter(prefix="/product")
r = redis.Redis.from_url(os.getenv("REDIS_URL"))


@router.get("/products", response_model=List[ProductSummaryResponse])  # 상품 목록 조회 (내가 장바구니에 담은 상품 제외)
def get_products(page: int = Query(..., ge=1), limit: int = Query(...), category: str = Query(...),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    saved_product_ids = db.query(ProductSave.product_id).filter(ProductSave.user_id == user.id).subquery()
    query = db.query(Product).filter(Product.id.not_in(saved_product_ids))
    if category != "전체":
        query = query.filter(Product.content.contains(category))

    products: List[Product] = (query.order_by(Product.created_at.desc()).offset(offset).limit(limit).all())
    
    response = []
    for product in products:
        response.append(build_product_summary_response(product, user.id))
    return response

@router.post("")  # 상품 등록
def create_product(
    name: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    saled_price: Optional[int] = Form(None),
    options: str = Form(...),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)):

    main_image = images[0]
    embedding = get_image_embedding(main_image)

    product = Product(
        user_id=user.id,
        name=name,
        content=content,
        category=category,
        price=price,
        saled_price=saled_price,
        embedding=embedding,
        is_sold=False,
        created_at=datetime.utcnow(),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    for i, image in enumerate(images):
        image_url = save_image(image, "products")
        product_image = ProductImage(
            product_id=product.id,
            imageURL=image_url,
            is_main=(i == 0)
        )
        db.add(product_image)

    try:
        option_dict = json.loads(options)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Option 형식이 틀림")

    for opt_name, opt_values in option_dict.items():
        option = Option(product_id=product.id, name=opt_name)
        db.add(option)
        db.commit()
        db.refresh(option)

        for value in opt_values:
            detail = OptionDetail(option_id=option.id, value=value)
            db.add(detail)

    db.commit()
    return {"message": "상품 등록 완료", "product_id": product.id}

@router.put("/{product_id}") # 상품 정보 수정 (일단 미완성.. main image 삭제&수정 시 embedding 문제 때문에)
def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    saled_price: Optional[int] = Form(None),
    remove_image_ids: List[int] = Form([]),
    new_images: List[UploadFile] = File([]),
    remove_option_names: List[str] = Form([]),
    new_options: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if name is not None:
        product.name = name
    if content is not None:
        product.content = content
    if category is not None:
        product.category = category
    if price is not None:
        product.price = price
    if saled_price is not None:
        product.saled_price = saled_price

    for image_id in remove_image_ids:
        image = db.query(ProductImage).filter_by(id=image_id, product_id=product.id).first()
        if image:
            delete_image(image.imageURL, "products")
            db.delete(image)

    for image in new_images:
        image_url = save_image(image, "products")
        is_main = not product.images  # 첫 이미지면 메인으로 설정
        db.add(ProductImage(product_id=product.id, imageURL=image_url, is_main=is_main))

        if is_main:
            embedding = get_image_embedding(image)
            product.embedding = embedding
            product.imageURL = image_url

    for option_name in remove_option_names:
        option = db.query(Option).filter_by(product_id=product.id, name=option_name).first()
        if option:
            db.delete(option)

    if new_options:
        try:
            parsed = json.loads(new_options)
            for name, values in parsed.items():
                option = Option(product_id=product.id, name=name)
                db.add(option)
                db.flush()

                for value in values:
                    db.add(OptionDetail(option_id=option.id, value=value))
        except Exception:
            raise HTTPException(status_code=400, detail="Option 형식이 틀림")

    db.commit()
    return {"message": "상품 수정 완료"}

@router.delete("/{product_id}")  # 상품 삭제
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "상품 삭제 완료"}

@router.get("/{product_id}", response_model=ProductResponse) # 특정 상품에 대한 상세 정보
def get_product_detail(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not Found")

    return build_product_response(product, user.id)

@router.get("/products/me", response_model=List[ProductSummaryResponse])  # 내 상품 목록
def get_my_products(page: int=Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    products: List[Product] = (db.query(Product).filter(Product.user_id == user.id).order_by(Product.created_at.desc()).offset(offset).limit(limit).all())

    response = []
    for product in products:
        response.append(build_product_summary_response(product, user.id))
    return response

@router.post("/{product_id}/like") # 상품 찜 (좋아요)
def like_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")

    already_liked = db.query(ProductLike).filter_by(product_id=product_id, user_id=user.id).first()
    if already_liked:
        db.delete(already_liked)
        product.likes -= 1
        is_liked = False
    else:
        new_like = ProductLike(product_id=product_id, user_id=user.id, created_at=datetime.utcnow())
        db.add(new_like)
        product.likes += 1
        is_liked = True

    db.commit()

    return {
        "is_liked": is_liked,
        "likes": product.likes
    }

@router.get("/products/saved", response_model=List[ProductSavedResponse]) # 장바구니에 추가한 상품 목록
def get_saved_products(page: int = Query(..., ge=1),limit: int = Query(...),db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    saved_product_ids = (db.query(ProductSave.product_id).filter(ProductSave.user_id == user.id).subquery())

    products: List[Product] = (db.query(Product).filter(Product.id.in_(saved_product_ids)).order_by(Product.created_at.desc()).offset(offset).limit(limit).all())
    
    response = [build_product_saved_response(product, user.id)for product in products]
    return response

@router.post("/{product_id}/save")  # 장바구니에 추가
def save_product(product_id: int, quantity: int = Query(1, ge=1), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    already_saved = db.query(ProductSave).filter(
        ProductSave.product_id == product_id,
        ProductSave.user_id == user.id
    ).first()

    price = product.price
    if product.saled_price:
        price = product.saled_price

    if already_saved:
        db.delete(already_saved)
        product.saves -= 1
        action = "unsaved"
    else:
        save = ProductSave(user_id=user.id, product_id=product_id, created_at=datetime.utcnow(), quantity=quantity,
                           total_price = price * quantity, selected_options = "")
        db.add(save)
        product.saves += 1
        action = "saved"

    db.commit()
    return {"is_saved": action == "saved", "saves": product.saves} 


