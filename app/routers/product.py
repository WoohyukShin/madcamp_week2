import os
import json
from app.schemas import *
from typing import List
from datetime import datetime
from fastapi import APIRouter, Form, File, UploadFile, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from app.models import *
from app.db.db import get_db
from app.utils.auth import get_current_user
from app.utils.image import save_image, delete_image
from app.utils.product import build_product_response, build_product_summary_response, build_product_saved_response, build_review_response

router = APIRouter(prefix="/product")

@router.get("/products", response_model=List[ProductSummaryResponse])  # 상품 목록 조회 (내가 장바구니에 담은 상품 제외)
def get_products(page: int = Query(..., ge=1), limit: int = Query(...), category: str = Query("all"),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * limit

    query = db.query(Product)
    if category != "all":
        query = query.filter(Product.category.contains(category))
        
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

    product = Product(
        user_id=user.id,
        name=name,
        content=content,
        category=category,
        price=price,
        saled_price=saled_price,
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

''' 상품 정보 수정 : 유기
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
'''
@router.delete("/{product_id}")  # 상품 삭제
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)

    db.commit()
    return {"message": "상품 삭제 완료"}

@router.get("/saved", response_model=List[ProductSavedResponse]) # 장바구니에 추가한 상품 목록
def get_saved_products(page: int = Query(..., ge=1),limit: int = Query(...),db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    offset = (page - 1) * limit
    print("Hello World!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
    saved_product_ids = (db.query(ProductSave.product_id).filter(ProductSave.user_id == user.id).subquery())

    products: List[Product] = (db.query(Product).filter(Product.id.in_(saved_product_ids)).order_by(Product.created_at.desc()).offset(offset).limit(limit).all())
    
    response = [build_product_saved_response(product, user.id)for product in products]
    return response

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


@router.post("/{product_id}/save")
def save_product(
    product_id: int,
    data: SaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    options = data.options
    quantity = data.quantity
    try:
        options_dict = json.loads(options)
    except Exception:
        raise HTTPException(status_code=400, detail="Option 형식이 틀림")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    already_saved = db.query(ProductSave).filter(
        ProductSave.product_id == product_id,
        ProductSave.user_id == user.id
    ).first()

    price = product.saled_price or product.price

    if already_saved:
        db.delete(already_saved)
        product.saves -= 1
        action = "unsaved"
    else:
        save = ProductSave(
            user_id=user.id,
            product_id=product_id,
            created_at=datetime.utcnow(),
            quantity=quantity,
            total_price=price * quantity,
            selected_options=options  # 👈 여기는 원문 string 저장해도 문제 없음
        )
        db.add(save)
        product.saves += 1
        action = "saved"

    db.commit()
    return {"is_saved": action == "saved", "saves": product.saves}

# 여기부터는 내가 안 함 ...
'''
@router.get("/product/saved", response_model=List[ProductSavedResponse])
def get_saved_products(
    page: int = Query(..., ge=1),
    limit: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    offset = (page - 1) * limit

    saved_items: List[ProductSave] = (
        db.query(ProductSave)
        .filter(ProductSave.user_id == user.id)
        .order_by(ProductSave.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []
    for item in saved_items:
        product = item.product
        main_image = next((img.imageURL for img in product.images if img.is_main), "")

        try:
            options_dict = json.loads(item.selected_options) if item.selected_options else {}
        except:
            options_dict = {}

        response.append(ProductSavedResponse(
            id=item.id,
            seller_id=product.user_id,
            product_id=product.id,
            seller=product.user.nickname,
            name=product.name,
            price=product.price,
            saled_price=product.saled_price,
            quantity=item.quantity,
            total_price=item.total_price,
            imageURL=main_image,
            is_sold=product.is_sold,
            options=options_dict
        ))

    return response
'''
@router.put("/saved/{product_save_id}")
def update_product_quantity(
    product_save_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    quantity = payload.get("quantity")
    if not isinstance(quantity, int) or quantity < 1:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    save = db.query(ProductSave).filter(
        ProductSave.id == product_save_id,
        ProductSave.user_id == user.id
    ).first()

    if not save:
        raise HTTPException(status_code=404, detail="Saved product not found")

    unit_price = save.product.saled_price if save.product.saled_price else save.product.price
    save.quantity = quantity
    save.total_price = quantity * unit_price
    db.commit()

    return {"unit_price": unit_price, "total_price": save.total_price}

@router.delete("/saved/{product_save_id}")
def delete_saved_product(
    product_save_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    save = db.query(ProductSave).filter(
        ProductSave.id == product_save_id,
        ProductSave.user_id == user.id
    ).first()

    if not save:
        raise HTTPException(status_code=404, detail="Saved product not found")

    db.delete(save)
    db.commit()
    return {"message": "삭제 완료"}

@router.post("/{product_id}/review")
def create_review(
    product_id: int,
    rating: int = Form(..., ge=1, le=5),
    content: str = Form(...),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    review = Review(
        product_id=product.id,
        user_id=user.id,
        rating=rating,
        content=content
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    for image in images:
        image_url = save_image(image, "reviews")
        db.add(ReviewImage(review_id=review.id, imageURL=image_url))

    # 평균 별점 & 리뷰 개수 업데이트
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    avg_rating = sum([r.rating for r in reviews]) / len(reviews)
    average_rating = round(avg_rating, 2)
    product.reviews = len(reviews)

    db.commit()

    return {
        "message": "리뷰 등록 완료",
        "review_id": review.id,
        "average_rating": average_rating,
        "ratings": product.reviews
    }

@router.put("/review/{review_id}")
def update_review(
    review_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user.id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    rating = payload.get("rating")
    content = payload.get("content")

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Invalid rating")

    review.rating = rating
    review.content = content
    db.commit()

    # 리뷰 통계 업데이트
    product = review.product
    reviews = db.query(Review).filter(Review.product_id == product.id).all()
    avg_rating = sum([r.rating for r in reviews]) / len(reviews)
    average_rating = round(avg_rating, 2)
    product.reviews = len(reviews)

    db.commit()

    return {
        "message": "리뷰 수정 완료",
        "average_rating": average_rating,
        "ratings": product.reviews
    }

@router.delete("/review/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user.id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    product = review.product
    db.delete(review)
    db.commit()

    # 리뷰 통계 다시 반영
    reviews = db.query(Review).filter(Review.product_id == product.id).all()
    if reviews:
        avg_rating = sum([r.rating for r in reviews]) / len(reviews)
        average_rating = round(avg_rating, 2)
        product.reviews = len(reviews)
    else:
        average_rating = 0.0
        product.reviews = 0

    db.commit()
    return {"message": "리뷰 삭제 완료"}


@router.get("/{product_id}/reviews", response_model=List[ReviewResponse])
def get_reviews_for_product(
    product_id: int,
    page: int = Query(..., ge=1),
    limit: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    offset = (page - 1) * limit

    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []
    for review in reviews:
        review_user = review.user
        review_images = [
            ReviewImageResponse(id=img.id, imageURL=img.imageURL)
            for img in review.images
        ]

        response.append(ReviewResponse(
            id=review.id,
            user_id=review_user.id,
            nickname=review_user.nickname,
            imageURL=review_user.imageURL,
            rating=review.rating,
            content=review.content,
            created_at=review.created_at,
            images=review_images
        ))

    return response

@router.post("/order")
def create_order(
    request: List[OrderRequest],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not request:
        raise HTTPException(status_code=400, detail="Empty order request")

    total_price = 0
    order_items = []

    for item in request:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        unit_price = product.saled_price if product.saled_price else product.price
        total = unit_price * item.quantity
        total_price += total

        order_items.append(OrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            selected_options=item.options,
            unit_price=unit_price
        ))

    # 주문 생성
    order = ProductOrder(
        user_id=user.id,
        total_price=total_price,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 주문 항목 저장
    for order_item in order_items:
        order_item.order_id = order.id
        db.add(order_item)

    db.commit()
    return {"order_id": order.id}

@router.get("/order/{order_id}", response_model=OrderResponse)
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(ProductOrder).filter(
        ProductOrder.id == order_id,
        ProductOrder.user_id == user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    item_responses = []
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        main_image = ""
        if product:
            main_image = next((img.imageURL for img in product.images if img.is_main), "")

        item_responses.append(OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            imageURL=main_image,
            quantity=item.quantity,
            selected_options=item.selected_options,
            unit_price=item.unit_price
        ))

    return OrderResponse(
        id=order.id,
        status=order.status,
        total_price=order.total_price,
        created_at=order.created_at,
        details=item_responses
    )
