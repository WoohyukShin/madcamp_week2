from app.db.db import Base
from sqlalchemy import String, Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref

class Feed(Base):
    __tablename__ = "Feed"

    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    content = Column(Text)
    created_at = Column(DateTime)
    likes = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    user = relationship("User", back_populates = "feeds")
    images = relationship("FeedImage", back_populates = "feed")
    comments = relationship("Comment", back_populates = "feed")
    feed_like = relationship("FeedLike", back_populates = "feed")
    feed_save = relationship("FeedSave", back_populates = "feed")

class FeedImage(Base):
    __tablename__ = "FeedImage"

    id = Column(Integer, primary_key = True, index = True)
    feed_id = Column(Integer, ForeignKey("Feed.id", ondelete = "CASCADE"))
    imageURL = Column(String)

    feed = relationship("Feed", back_populates = "images")

class Comment(Base):
    __tablename__ = "Comment"

    id = Column(Integer, primary_key = True, index = True)
    feed_id = Column(Integer, ForeignKey("Feed.id", ondelete = "CASCADE"))
    user_id = Column(Integer, ForeignKey("User.id", ondelete = "CASCADE"))
    parent_id = Column(Integer, ForeignKey("Comment.id", ondelete = "CASCADE"))
    content = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    likes = Column(Integer, default=0)
    
    feed = relationship("Feed", back_populates = "comments", passive_deletes = True)
    user = relationship("User", back_populates = "comments", passive_deletes = True)
    replies = relationship(
        "Comment",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan"
    )