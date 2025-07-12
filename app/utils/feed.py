from app.models import *
from app.schemas import *

def build_comment_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=[ build_comment_response(reply) for reply in comment.replies ]
    )