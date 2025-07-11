from app.db.db import Base
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Follow(Base):
    __tablename__ = "Follow"
    id = Column(Integer, primary_key = True, index = True)
    follower_id = Column(Integer, ForeignKey("User.id"), ondelete = "CASCADE")
    followee_id = Column(Integer, ForeignKey("User.id"), ondelete = "CASCADE")
    created_at = Column(DateTime)

class FeedLike(Base):
    __tablename__ = "FeedLike"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id"), ondelete = "CASCADE")
    feed_id = Column(Integer, ForeignKey("Feed.id"), ondelete = "CASCADE")
    created_at = Column(DateTime)

    feed = relationship("Feed", back_populates = "feed_like")
    liked_user = relationship("User", back_populates = "feed_like")

class FeedSave(Base):
    __tablename__ = "FeedSave"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id"), ondelete = "CASCADE")
    feed_id = Column(Integer, ForeignKey("Feed.id"), ondelete = "CASCADE")
    created_at = Column(DateTime)

    feed = relationship("Feed", back_populates = "feed_save")
    saved_user = relationship("User", back_populates = "feed_save")

class CommentLike(Base):
    __tablename__ = "CommentLike"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id"), ondelete = "CASCADE")
    comment_id = Column(Integer, ForeignKey("Comment.id"), ondelete = "CASCADE")
    created_at = Column(DateTime)

    