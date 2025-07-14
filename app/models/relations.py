from app.db.db import Base
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
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
'''
class ProductSave(Base): # 장바구니
    __tablename__ = "ProductSave"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    product_id = Column(Integer, ForeignKey("Product.id", ondelete = "CASCADE"))
    created_at = Column(DateTime)
    quantity = Column(Integer, nullable=False)
    selected_options = Column(str) # 이거는 옵션 바꿀 때마다 string으로 만들어서 반환하는 함수 utils/에 만들어야 할 듯?

    product = relationship("Product", back_populates = "product_save")
    saved_user = relationship("User", back_populates = "product_save")

class ProductLike(Base):
    __tablename__ = "ProductLike"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Product.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE"))
    created_at = Column(DateTime)

    product = relationship("Product", back_populates="product_like")
    liked_user = relationship("User", back_populates="product_like")
'''