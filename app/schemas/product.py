from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ProductImageResponse(BaseModel):
    id: int
    imageURL: str

class ReviewImageResponse(BaseModel):
    id: int
    imageURL: str

class ReviewResponse(BaseModel):
    id: int
    user_id: int # 작성자 id
    nickname: str # 작성자 닉네임
    imageURL: str # 작성자 profile Image
    rating: int # 별점
    content: str
    created_at: datetime
    images: List[ReviewImageResponse]

class ProductSummaryResponse(BaseModel):
    id: int
    seller: str             # 판매자 닉네임
    name: str               # 상품 이름
    price: int              # 가격
    saled_price: Optional[int] = None # 할인 가격
    imageURL: str           # 대표 이미지 URL
    is_sold: bool           # 품절 여부
    likes: int              # 좋아요 수
    user_likes: bool
    ratings: int            # 별점 개수
    average_rating: float   # 평균 별점

class ProductResponse(BaseModel): # 상품 상세정보 탭에서 return하는 정보
    id: int
    user_id: int
    seller: str # 판매자 닉네임
    name: str # 상품 이름
    content: str # 상품 설명
    price: int # 상품 가격
    saled_price: Optional[int] = None # 할인이라면 할인된 가격
    images: List[ProductImageResponse] # 상품 이미지들
    created_at: datetime
    is_sold: bool # 품절 여부
    saves: int
    user_saves: bool
    likes: int
    user_likes: bool
    ratings: int # 별점 개수
    average_rating: float # 평균 별점
    options: Dict[str, List[str]] # ex) {"색상":["화이트","골드"], "크기":["L","M"] }
    reviews: List[ReviewResponse] # Reviews

class ProductSavedResponse(BaseModel): # 장바구니 정보
    id: int
    seller_id: int # 판매자 ID
    product_id: int # 상품 ID
    seller: str # 판매자 닉네임
    name: str # 상품 이름
    price: int # 상품 가격
    saled_price: Optional[int] = None # 할인이라면 할인된 가격
    quantity: int # 개수
    total_price: int # 총 가격
    imageURL: str # 대표 이미지 URL
    is_sold: bool # 품절 여부
    options: Dict[str, str] # ex) {"색상":"화이트", "크기":"L" }

class OrderRequest(BaseModel):
    id: int
    product_id: int
    quantity: int
    options: str

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    imageURL: str
    quantity: int
    selected_options: str
    unit_price: int

class OrderResponse(BaseModel):
    id: int
    status: str
    total_price: int
    created_at: datetime
    details: List[OrderItemResponse]

