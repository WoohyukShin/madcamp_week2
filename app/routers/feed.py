import os
import json
import redis
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.image import save_image, delete_image
from app.utils.feed import build_comment_response

router = APIRouter(prefix="/feed")

@router.get("/feeds") # 몇 번째 요청인지에 따라서 Feed 반환해 주는 함수
def get_feeds(page: int=Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user:User=Depends(get_current_user), 
              response_model = List[FeedResponse]):
    offset = (page - 1) * limit
    following = [u.id for u in user.following]
    feeds: List[Feed] = (
        db.query(Feed).filter(Feed.user_id.in_(following))
        .order_by(Feed.created_at.desc()).offset(offset).limit(limit).all()
    )

    response = []
    for feed in feeds:
        response.append(FeedResponse(
            id=feed.id,
            user_id=feed.user_id,
            content=feed.content,
            created_at=feed.created_at,
            likes=feed.likes,
            saves=feed.saves,
            images=[
                FeedImageResponse(id=image.id, imageURL=image.imageURL)
                for image in feed.images
            ],
            comments=[
                build_comment_response(comment)
                for comment in feed.comments
                if comment.parent_id is None
            ]
        ))

    return response

@router.get("/feeds/me") # 내 피드
def get_my_feeds(page: int = Query(1, ge=1),db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    limit = 10
    offset = (page - 1) * limit

    feeds: List[Feed] = (
        db.query(Feed)
        .filter(Feed.user_id == user.id)
        .order_by(Feed.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []
    for feed in feeds:
        response.append(FeedResponse(
            id=feed.id,
            user_id=feed.user_id,
            content=feed.content,
            created_at=feed.created_at,
            likes=feed.likes,
            saves=feed.saves,
            images=[
                FeedImageResponse(id=image.id, imageURL=image.imageURL)
                for image in feed.images
            ],
            comments=[
                build_comment_response(comment)
                for comment in feed.comments
                if comment.parent_id is None
            ]
        ))
    return response

@router.post("/feeds") # 피드 작성
def create_feed(content: str = Form(...),images: List[UploadFile] = File([]),
                db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    feed = Feed(
        user_id=user.id,
        content=content,
        created_at=datetime.utcnow(),
        likes=0,
        saves=0
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)

    for image in images:
        image_url = save_image(image, "feeds")
        db.add(FeedImage(feed_id=feed.id, imageURL=image_url))

    db.commit()
    return {"message": "Feed created", "feed_id": feed.id}

@router.put("/feeds/{feed_id}") # 피드 수정
def update_feed(
    feed_id: int,
    content: str = Form(...),
    remove_image_ids: List[int] = Form([]),
    new_images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    feed = db.query(Feed).filter(Feed.id == feed_id, Feed.user_id == user.id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    feed.content = content
    for image_id in remove_image_ids:
        img = db.query(FeedImage).filter(FeedImage.id == image_id, FeedImage.feed_id == feed_id).first()
        if img:
            imageURL = img.imageURL
            db.delete(img)
            delete_image(imageURL, "feeds")

    for img in new_images:
        image_url = save_image(img, "feeds")
        db.add(FeedImage(feed_id=feed.id, imageURL=image_url))

    db.commit()
    return { "message": "Feed updated" }

@router.delete("/feeds/{feed_id}") # 피드 삭제
def delete_feed(feed_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    feed = db.query(Feed).filter(Feed.id == feed_id, Feed.user_id == user.id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="No permission or feed not found")

    for img in feed.images:
        imageURL = img.imageURL
        delete_image(imageURL, "feeds")
        db.delete(img)

    db.delete(feed)
    db.commit()
    return {"message": "Feed deleted"}

@router.post("/feeds/{feed_id}/like") # 피드 좋아요
def like_feed(feed_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    already_like = (db.query(FeedLike).filter(FeedLike.feed_id == feed_id, FeedLike.user_id == user.id).first())

    if already_like:
        db.delete(already_like)
        feed.likes -= 1
        action = "unliked"
    else:
        feedlike = FeedLike(user_id=user.id, feed_id=feed_id, created_at=datetime.utcnow())
        db.add(feedlike)
        feed.likes += 1
        action = "liked"

    db.commit()
    return {"message": f"Feed {action}", "likes": feed.likes}

@router.post("/feeds/{feed_id}/save")  # 피드 저장
def save_feed(feed_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    already_saved = (db.query(FeedSave).filter(FeedSave.feed_id == feed_id, FeedSave.user_id == user.id).first())

    if already_saved:
        db.delete(already_saved)
        feed.saves -= 1
        action = "unsaved"
    else:
        feed_save = FeedSave(user_id=user.id, feed_id=feed_id, created_at=datetime.utcnow())
        db.add(feed_save)
        feed.saves += 1
        action = "saved"

    db.commit()
    return {"message": f"Feed {action}"}

@router.post("/feeds/{feed_id}/comments") # 댓글 작성
def create_comment(feed_id: int, req: CommentCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    comment = Comment(
        feed_id=feed_id,
        user_id=user.id,
        content=req.content,
        parent_id=req.parent_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return { "message": "Comment created", "comment_id": comment.id }

@router.post("/comments/{comment_id}/like") # 댓글 좋아요 or 좋아요 취소
def toggle_comment_like(comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    already_like = (db.query(CommentLike).filter(CommentLike.comment_id == comment_id, CommentLike.user_id == user.id).first())

    if already_like:
        db.delete(already_like)
        comment.likes -= 1
        action = "unliked"
    else:
        new_like = CommentLike(comment_id=comment_id, user_id=user.id, created_at=datetime.utcnow())
        db.add(new_like)
        comment.likes += 1
        action = "liked"

    db.commit()
    return {"message": f"Comment {action}", "likes": comment.likes}

@router.put("/comments/{comment_id}") # 댓글 수정
def update_comment(comment_id: int, req: CommentEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment or comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="No permission or comment not found")

    comment.content = req.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Comment updated"}

@router.delete("/comments/{comment_id}") # 댓글 삭제
def delete_comment(comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment or comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="No permission or comment not found")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}

