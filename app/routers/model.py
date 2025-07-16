import os
from typing import Dict, List
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.product import build_product_summary_response

router = APIRouter(prefix="/model")

@router.post("/recommend/text", response_model=Dict[str, List[ProductSummaryResponse]])
def get_recommendation_from_text(
    text: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # 여기에 Gemini API를 호출하고, 추천 로직을 구현합니다.
    # 현재는 임시로 빈 결과를 반환합니다.
    
    # 예시: Gemini API를 통해 추천 카테고리와 키워드를 얻는다고 가정
    # recommended_categories = call_gemini_api(text)
    
    # 임시 추천 로직: 모든 상품을 반환
    products = db.query(Product).all()
    
    recommendations = {
        "recommended": [build_product_summary_response(p, user.id) for p in products]
    }
    
    return recommendations
