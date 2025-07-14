from app.models import *
from app.schemas import *

def build_comment_response(comment: Comment, user_id: int) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        user_id=comment.user.id,
        nickname=comment.user.nickname,
        content=comment.content,
        created_at=comment.created_at,
        likes=comment.likes,
        user_likes=any(like.user_id == user_id for like in comment.comment_like),
        updated_at=comment.updated_at,
        replies=[ build_comment_response(reply, user_id) for reply in comment.replies ]
    )