from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user

router = APIRouter(prefix="/comment")

@router.post("/{comment_id}/like") # 댓글 좋아요 or 좋아요 취소
def like_comment(comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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
    return {"is_liked": action == "liked", "likes": comment.likes}

@router.put("/{comment_id}") # 댓글 수정
def update_comment(comment_id: int, req: CommentEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment or comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="No permission or comment not found")

    comment.content = req.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Comment updated"}

@router.delete("/{comment_id}") # 댓글 삭제
def delete_comment(comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment or comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="No permission or comment not found")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}

