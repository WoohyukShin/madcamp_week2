import os
import json
import random
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.db.db import SessionLocal
from app.models import User
from app.models.product import Product, ProductImage
from app.utils.image import save_image
from starlette.datastructures import UploadFile as StarletteUploadFile


def bulk_create_from_json():
    db = SessionLocal()

    current_dir = os.path.dirname(__file__)
    json_path = os.path.join(current_dir, "furniture_data.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        filename = item["filename"]
        color = item["color"]
        style = item["style"]
        category = item["category"]

        price = random.randrange(10000, 300000 + 1, 10000)
        saled_price = random.randrange(10000, price + 1, 10000)

        product = Product(
            user_id=1,
            name=filename,
            content=f"{style} {color} 제품입니다.",
            category=category,
            price=price,
            saled_price=saled_price,
            is_sold=False,
            created_at=datetime.utcnow()
        )

        db.add(product)
        db.flush()  # product.id 확보용

        image_url = f"https://madcamp-whshin-week2.s3.ap-northeast-2.amazonaws.com/products/{filename}"
        product_image = ProductImage(
            product_id=product.id,
            imageURL=image_url,
            is_main=True
        )
        db.add(product_image)

    db.commit()
    db.close()
    print("✅ 모든 product 및 이미지 등록 완료.")
