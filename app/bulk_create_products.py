import os
import json
import boto3
from uuid import uuid4
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

from app.db.db import SessionLocal
from app.models import Product, ProductImage, Option, OptionDetail, User

# --- S3 설정 ---
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# --- 데이터 정의 ---
# 여기에 대량으로 추가할 상품 데이터를 정의합니다.
# 이미지 경로는 'app/bulk_images/' 폴더를 기준으로 작성합니다.
PRODUCTS_DATA = [
    {
        "name": "모던 스타일 의자",
        "content": "미니멀하고 세련된 디자인의 의자입니다.",
        "category": "의자",
        "price": 85000,
        "saled_price": 79000,
        "options": {
            "색상": ["블랙", "화이트", "그레이"],
            "재질": ["플라스틱", "스틸"]
        },
        "images": ["chair1.jpg", "chair2.jpg"]
    },
    {
        "name": "원목 책상",
        "content": "따뜻한 느낌을 주는 튼튼한 원목 책상입니다.",
        "category": "책상",
        "price": 250000,
        "saled_price": None,
        "options": {
            "크기": ["1200x600", "1400x700"]
        },
        "images": ["desk1.jpg"]
    },
    # ... 여기에 더 많은 상품 추가
]

def upload_local_image_to_s3(file_path: str, folder_name: str) -> str:
    """로컬 이미지 파일을 S3에 업로드하고 URL을 반환합니다."""
    try:
        ext = file_path.split(".")[-1]
        filename = f"{folder_name}/{uuid4().hex}.{ext}"
        
        with open(file_path, "rb") as f:
            s3.upload_fileobj(
                f,
                AWS_S3_BUCKET,
                filename,
                ExtraArgs={"ContentType": f"image/{ext}"}
            )
        
        image_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        return image_url
    except FileNotFoundError:
        print(f"[Error] 파일을 찾을 수 없습니다: {file_path}")
        return None
    except Exception as e:
        print(f"[Error] S3 업로드 실패: {e}")
        return None

def bulk_create_products():
    """정의된 데이터를 기반으로 상품을 대량 생성합니다."""
    db: Session = SessionLocal()
    print("대량 상품 등록을 시작합니다...")

    # 상품을 등록할 판매자(유저)를 가져옵니다. 여기서는 첫 번째 유저를 사용합니다.
    seller = db.query(User).first()
    if not seller:
        print("[Error] 상품을 등록할 유저가 데이터베이스에 없습니다. 스크립트를 종료합니다.")
        db.close()
        return

    # 이미지 파일들이 위치한 기본 경로
    base_image_path = os.path.join(os.path.dirname(__file__), 'bulk_images')

    for product_data in PRODUCTS_DATA:
        print(f"'{product_data['name']}' 상품 등록 중...")

        # 1. Product 생성
        new_product = Product(
            user_id=seller.id,
            name=product_data["name"],
            content=product_data["content"],
            category=product_data["category"],
            price=product_data["price"],
            saled_price=product_data.get("saled_price"),
        )
        db.add(new_product)
        db.flush()  # product.id를 얻기 위해 flush

        # 2. ProductImage 생성
        for i, image_filename in enumerate(product_data["images"]):
            local_path = os.path.join(base_image_path, image_filename)
            image_url = upload_local_image_to_s3(local_path, "products")
            
            if image_url:
                new_image = ProductImage(
                    product_id=new_product.id,
                    imageURL=image_url,
                    is_main=(i == 0)
                )
                db.add(new_image)

        # 3. Option 및 OptionDetail 생성
        if "options" in product_data:
            for opt_name, opt_values in product_data["options"].items():
                new_option = Option(product_id=new_product.id, name=opt_name)
                db.add(new_option)
                db.flush() # option.id를 얻기 위해 flush

                for value in opt_values:
                    new_detail = OptionDetail(option_id=new_option.id, value=value)
                    db.add(new_detail)
    
    try:
        db.commit()
        print("\n모든 상품이 성공적으로 등록되었습니다!")
    except Exception as e:
        print(f"\n[Error] 데이터베이스 커밋 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # 이 스크립트를 직접 실행할 때 bulk_create_products 함수가 호출됩니다.
    # 예: python -m app.bulk_create_products
    bulk_create_products()
