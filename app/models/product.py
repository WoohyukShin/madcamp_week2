import json
from app.db.db import Base
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

class Product(Base):
    __tablename__ = "Product"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False) # 상품 이름
    content = Column(String, nullable=True) # 상품 설명
    # 카테고리 : bed, desk, cabinet, chair, etc
    category = Column(String, default="기타")
    # 가격, 세일된 가격
    price = Column(Integer, nullable=False) # 가격
    saled_price = Column(Integer, nullable=True, default = 0)
    # 상품 이미지, created_at
    created_at = Column(DateTime, default=datetime.utcnow)
    # 찜, 장바구니, 리뷰, 옵션 개수
    saves = Column(Integer, default = 0)
    likes = Column(Integer, default = 0)
    reviews = Column(Integer, default = 0)
    options = Column(Integer, default = 0)
    # 벡터 임베딩, 품절 여부
    embedding = Column(Text, nullable=True)  # 메인 이미지의 임베딩
    is_sold = Column(Boolean, default=False)

    user = relationship("User", back_populates="products")
    product_save = relationship("ProductSave", back_populates="product")
    product_like = relationship("ProductLike", back_populates="product")
    product_review = relationship("Review", back_populates="product")
    product_option = relationship("Option", back_populates="product")
    images = relationship("ProductImage", back_populates = "product")

    @property
    def embedding_vector(self):
        return json.loads(self.embedding) if self.embedding else None

    @embedding_vector.setter
    def embedding_vector(self, vector):
        self.embedding = json.dumps(vector)

class ProductImage(Base):
    __tablename__ = "ProductImage"

    id = Column(Integer, primary_key = True, index = True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete = "CASCADE"))
    imageURL = Column(String)
    is_main = Column(Boolean) # 메인 이미지만 임베딩할 예정? 이거 어떻게 하지

    product = relationship("Product", back_populates = "images")

class Review(Base):
    __tablename__ = "Review"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1~5점 정수
    content = Column(String, nullable=True) # 리뷰글
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="product_review")
    images = relationship("ReviewImage", back_populates = "review")
    user = relationship("User", back_populates="reviews")

class ReviewImage(Base):
    __tablename__ = "ReviewImage"

    id = Column(Integer, primary_key = True, index = True)
    review_id = Column(Integer, ForeignKey("Review.id", ondelete = "CASCADE"))
    imageURL = Column(String)

    review = relationship("Review", back_populates = "images")

class Option(Base):
    __tablename__ = "Option"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="CASCADE"))
    name = Column(String, nullable=False) # "색상", "사이즈"

    product = relationship("Product", back_populates="product_option")
    details = relationship("OptionDetail", back_populates="option")

class OptionDetail(Base):
    __tablename__ = "OptionDetail"
    id = Column(Integer, primary_key=True, index=True)
    option_id = Column(Integer, ForeignKey("Option.id", ondelete="CASCADE"))
    value = Column(String) # "빨강" "140cm" "Large"

    option = relationship("Option", back_populates="details")
