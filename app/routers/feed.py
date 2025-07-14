import os
import json
import redis
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.image import save_image, delete_image
from app.utils.feed import build_comment_response
from app.utils.model import get_image_embedding


router = APIRouter(prefix="/feed")

@router.get("/feeds") # 몇 번째 요청인지에 따라서 Feed 반환해 주는 함수
def get_feeds(page: int=Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user:User=Depends(get_current_user), 
              response_model = List[FeedResponse]):
    offset = (page - 1) * limit
    following = [u.id for u in user.following]
    following.append(user.id)

    feeds: List[Feed] = (db.query(Feed).order_by(Feed.created_at.desc()).offset(offset).limit(limit).all())

    response = []
    for feed in feeds:
        response.append(FeedResponse(
            id=feed.id,
            user_id=feed.user.id,
            nickname=feed.user.nickname,
            content=feed.content,
            created_at=feed.created_at,
            likes=feed.likes,
            saves=feed.saves,
            user_likes = any(like.user_id == user.id for like in feed.feed_like),
            user_saves = any(save.user_id == user.id for save in feed.feed_save),
            images=[
                FeedImageResponse(id=image.id, imageURL=image.imageURL)
                for image in feed.images
            ],
            comments=[
                build_comment_response(comment, user.id)
                for comment in feed.comments
                if comment.parent_id is None
            ]
        ))

    return response

@router.get("/{feed_id}/comments") # 특정 피드의 comments 모두 반환해주는 함수
def get_comments(feed_id: int, page: int = Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user:User=Depends(get_current_user)):
    offset = (page - 1) * limit

    comments = (
        db.query(Comment)
        .filter(Comment.feed_id == feed_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    top_level_comments = [c for c in comments if c.parent_id is None]
    paginated_comments = top_level_comments[offset:offset + limit]

    return [build_comment_response(comment, user.id) for comment in paginated_comments]

@router.get("/feeds/me") # 내 피드
def get_my_feeds(page: int = Query(1, ge=1), limit: int=Query(...), db: Session = Depends(get_db),user: User = Depends(get_current_user)):
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
            user_id=feed.user.id,
            nickname=feed.user.nickname,
            content=feed.content,
            created_at=feed.created_at,
            likes=feed.likes,
            saves=feed.saves,
            user_likes = any(like.user_id == user.id for like in feed.feed_like),
            user_saves = any(save.user_id == user.id for save in feed.feed_save),
            images=[
                FeedImageResponse(id=image.id, imageURL=image.imageURL)
                for image in feed.images
            ],
            comments=[
                build_comment_response(comment, user.id)
                for comment in feed.comments
                if comment.parent_id is None
            ]
        ))
    return response

@router.get("/feeds/saved") # 내가 저장한 피드
def get_saved_feeds(page: int=Query(..., ge=1), limit: int = Query(...), db: Session = Depends(get_db), user:User=Depends(get_current_user), 
              response_model = List[FeedResponse]):
    offset = limit * (page - 1)
    feeds: List[Feed] = (
        db.query(Feed)
        .join(FeedSave, Feed.id == FeedSave.feed_id)
        .filter(FeedSave.user_id == user.id)
        .order_by(Feed.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []
    for feed in feeds:
        response.append(FeedResponse(
            id=feed.id,
            user_id=feed.user.id,
            nickname=feed.user.nickname,
            content=feed.content,
            created_at=feed.created_at,
            likes=feed.likes,
            saves=feed.saves,
            user_likes = any(like.user_id == user.id for like in feed.feed_like),
            user_saves = True,
            images=[
                FeedImageResponse(id=image.id, imageURL=image.imageURL)
                for image in feed.images
            ],
            comments=[
                build_comment_response(comment, user.id)
                for comment in feed.comments
                if comment.parent_id is None
            ]
        ))
    return response

@router.post("") # 피드 작성
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
        embedding = get_image_embedding(image) # 혹시나 잘못되면 일단 이거 추가해서 잘못된 거일 수도?
        image_url = save_image(image, "feeds")
        feedimage = FeedImage(feed_id=feed.id, imageURL=image_url)
        db.add(feedimage)
        # db.add(ImageEmbedding(image_id=feedimage.id, embedding=embedding))

    db.commit()
    return {"message": "Feed created", "feed_id": feed.id}

@router.put("/{feed_id}") # 피드 수정
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
        embedding = get_image_embedding(img)
        image_url = save_image(img, "feeds")
        feedimage = FeedImage(feed_id=feed.id, imageURL=image_url)
        db.add(feedimage)
        # db.add(ImageEmbedding(image_id=feedimage.id, embedding=embedding))

    db.commit()
    return { "message": "Feed updated" }

@router.delete("/{feed_id}") # 피드 삭제
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

@router.post("/{feed_id}/like") # 피드 좋아요
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
    return {"is_liked": action == "liked", "likes": feed.likes}

@router.post("/{feed_id}/save")  # 피드 저장
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
    return {"is_saved": action == "saved", "saves": feed.saves}

@router.post("/{feed_id}/comment") # 댓글 작성
def create_comment(feed_id: int, req: CommentCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    print(feed_id)
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

