from app.models import *
from app.schemas import *
from datetime import datetime
from fastapi import HTTPException

def build_product_summary_response(product: Product, user_id: int) -> ProductSummaryResponse:
    return ProductSummaryResponse(
        id=product.id,
        seller=product.user.nickname,
        name=product.name,
        price=product.price,
        content=product.content,
        saled_price=product.saled_price,
        imageURL=next((img.imageURL for img in product.images if img.is_main), ""),
        is_sold=product.is_sold,
        likes=product.likes,
        user_likes=any(l.user_id == user_id for l in product.product_like),
        ratings=len(product.product_review),
        average_rating = (
            round(sum(r.rating for r in product.product_review) / len(product.product_review), 1)
            if product.product_review else 0.0
        )
    )

def build_product_response(product: Product, user_id: int) -> ProductResponse:
    options_dict = {}
    ratings = [review.rating for review in product.product_review]

    for option in product.product_option:
        key = option.name
        values = [detail.value for detail in option.details]
        options_dict[key] = values

    return ProductResponse(
        id = product.id,
        user_id = product.user_id,
        seller = product.user.nickname,
        name = product.name,
        content = product.content,
        category = product.category,
        price = product.price,
        saled_price = product.saled_price,
        imageURL = next((img.imageURL for img in product.images if img.is_main), ""),
        images=[ProductImageResponse(id=image.id, imageURL=image.imageURL) for image in product.images],
        created_at = product.created_at,
        is_sold = product.is_sold,
        saves = product.saves,
        likes = product.likes,
        user_saves = any(save.user_id == user_id for save in product.product_save),
        user_likes = any(like.user_id == user_id for like in product.product_like),
        ratings = len(product.product_review),
        average_rating = (
            round(sum(r.rating for r in product.product_review) / len(product.product_review), 1)
            if product.product_review else 0.0
        ),
        options = options_dict,
        reviews=[build_review_response(r) for r in product.product_review]
    )

def build_product_saved_response(product: Product, user_id: int) -> ProductSavedResponse:
    saved_entry = next(
        (save for save in product.product_save if save.user_id == user_id),
        None
    )
    if not saved_entry:
        raise HTTPException(status_code=404, detail="장바구니 정보가 없습니다.")
    
    main_image = next((img.imageURL for img in product.images if img.is_main), None)

    options = {}
    if saved_entry.selected_options:
        try:
            import json
            raw_options = json.loads(saved_entry.selected_options)
            options = {
                k: v[0] if isinstance(v, list) else v
                for k, v in raw_options.items()
            }
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=500, detail="선택된 옵션 형식이 잘못되었습니다.")

    return ProductSavedResponse(
        id=saved_entry.id,
        seller_id=product.user_id,
        product_id=product.id,
        seller=product.user.nickname,
        name=product.name,
        price=product.price,
        saled_price=product.saled_price,
        quantity=saved_entry.quantity,
        total_price=saved_entry.total_price,
        imageURL=main_image,
        is_sold=product.is_sold,
        options=options
    )

def build_review_response(review: Review) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        nickname=review.user.nickname,
        imageURL=review.user.imageURL or "",
        rating=review.rating,
        content=review.content,
        created_at=review.created_at,
        images=[
            ReviewImageResponse(
                id=img.id,
                imageURL=img.imageURL
            )
            for img in review.images
        ]
    )
