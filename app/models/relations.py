from datetime import datetime
from app.db.db import Base
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

class Follow(Base):
    __tablename__ = "Follow"
    id = Column(Integer, primary_key = True, index = True)
    follower_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    followee_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    created_at = Column(DateTime)

class FeedLike(Base):
    __tablename__ = "FeedLike"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    feed_id = Column(Integer, ForeignKey("Feed.id", ondelete = "CASCADE"))
    created_at = Column(DateTime)

    feed = relationship("Feed", back_populates = "feed_like")
    liked_user = relationship("User", back_populates = "feed_like")

class FeedSave(Base):
    __tablename__ = "FeedSave"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    feed_id = Column(Integer, ForeignKey("Feed.id", ondelete = "CASCADE"))
    created_at = Column(DateTime)

    feed = relationship("Feed", back_populates = "feed_save")
    saved_user = relationship("User", back_populates = "feed_save")

class CommentLike(Base):
    __tablename__ = "CommentLike"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    comment_id = Column(Integer, ForeignKey("Comment.id", ondelete = "CASCADE"))
    created_at = Column(DateTime)
    comment = relationship("Comment", back_populates = "comment_like")

class ProductLike(Base): # 찜한 상품
    __tablename__ = "ProductLike"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"))
    created_at = Column(DateTime)

    product = relationship("Product", back_populates="product_like")
    liked_user = relationship("User", back_populates="product_like")

class ProductSave(Base): # 장바구니
    __tablename__ = "ProductSave"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    product_id = Column(Integer, ForeignKey("Product.id", ondelete = "CASCADE"))
    created_at = Column(DateTime)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer)
    selected_options = Column(String)

    product = relationship("Product", back_populates = "product_save")
    saved_user = relationship("User", back_populates = "product_save")

class ProductOrder(Base): # Total Order
    __tablename__ = "ProductOrder"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    status = Column(String, default="pending")  # 예: pending, paid, canceled
    total_price = Column(Integer, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base): # 상품 하나하나의 개별적 주문
    __tablename__ = "OrderItem"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("ProductOrder.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="SET NULL"))

    quantity = Column(Integer)
    selected_options = Column(String)
    unit_price = Column(Integer)

    order = relationship("ProductOrder", back_populates="items")
    product = relationship("Product")