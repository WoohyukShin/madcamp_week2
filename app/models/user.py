import enum
from app.db.db import Base
from app.models.relations import Follow
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    imageURL = Column(String, nullable=True)
    nickname = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    birthday = Column(DateTime)
    gender = Column(String)
    auth_type = Column(String, nullable=False)

    following = relationship (
        "User",
        secondary=Follow.__table__,
        primaryjoin=(id == Follow.follower_id),
        secondaryjoin=(id == Follow.followee_id),
        back_populates="followers"
    )
    followers = relationship(
        "User",
        secondary=Follow.__table__,
        primaryjoin=(id == Follow.followee_id),
        secondaryjoin=(id == Follow.follower_id),
        back_populates="following"
    )
    feeds = relationship("Feed", back_populates = "user")
    comments = relationship("Comment", back_populates = "user")
    feed_like = relationship("FeedLike", back_populates = "liked_user")
    feed_save = relationship("FeedSave", back_populates = "saved_user")
    products = relationship("Product", back_populates="user")
    product_like = relationship("ProductLike", back_populates="liked_user")
    product_save = relationship("ProductSave", back_populates="saved_user")
    orders = relationship("ProductOrder", back_populates="user")