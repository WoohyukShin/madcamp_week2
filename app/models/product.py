'''
from app.db.db import Base
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from datetime import datetime

class Product(Base):
    __tablename__ = "Product"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(String, nullable=True) # 상품 설명

    price = Column(Integer, nullable=False) # 가격
    saled_price = Column(Integer, nullable=True) # 세일된 가격


    imageURL = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    saves = Column(Integer, default = 0)
    likes = Column(Integer, default = 0)

    embedding = Column(Vector(512), nullable=True)  # CLIP 등과 연동 가능한 vector 타입?
    is_sold = Column(Boolean, default=False)

    user = relationship("User", back_populates="products")
    product_save = relationship("ProductSave", back_populates="product")
    product_like = relationship("ProductLike", back_populates="product")
    options = relationship("Option", back_populates="product")
    reviews = relationship("Review", back_populates="product")


class Review(Base):
    __tablename__ = "Review"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1~5점 정수
    content = Column(str, nullable=True) # 리뷰
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User")

class Option(Base):
    __tablename__ = "Option"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)  # 예: "색상", "사이즈"
    value = Column(String, nullable=False)  # 예: "Red", "Large"

    product = relationship("Product", back_populates="options")

class Order(Base):
    __tablename__ = "Order"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # 예: pending, paid, canceled

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

'''