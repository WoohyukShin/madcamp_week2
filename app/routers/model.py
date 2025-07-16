import os
from typing import Dict, List
from fastapi import APIRouter, Form, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.product import build_product_summary_response

import google.generativeai as genai
from PIL import Image

# genai.configure(api_key="YOUR_API_KEY")

def gemini_generate(prompt: str, img_bytes: bytes) -> str:
    # 이 함수는 예시이며, 실제 API 키와 모델 설정을 해야 합니다.
    try:
        model = genai.GenerativeModel('gemini-pro-vision')
        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": img_bytes
            }
        ]
        prompt_parts = [prompt, image_parts[0]]
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        # 실제 운영 환경에서는 더 상세한 에러 로깅이 필요합니다.
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")


router = APIRouter(prefix="/model")

@router.post("/recommend/text", response_model=dict)
def get_recommendation_from_text(
    style: str = Form(...),
    color: str = Form(...),
    image: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    prompt = f'''
        나는 지금 {color} 톤의 {style} 스타일로 내 방을 꾸미고 싶어. 참고를 위해 내 방 사진도 함께 첨부할게.

        내 방 사진을 분석해서, 아래에 명시된 카테고리 중 내 스타일과 톤에 어울리지 않는 가구들을 찾아줘. 각 가구가 어울리지 않는 이유도 간단히 설명해 줘.

        출력 형식은 반드시 아래와 같이 JSON으로 파싱 가능한 딕셔너리 형태로 해줘:

        "의자": "현재 의자는 너무 화려해서 모던 스타일과 조화롭지 않습니다.",
        "수납": "서랍의 색상이 전체 톤과 맞지 않아 이질감이 듭니다.",
        "기타": "전체적으로 고전적인 느낌의 가구들이 섞여 있어 스타일이 혼재되어 보입니다."

        사용 가능한 카테고리는 다음으로 제한해:
        "침대", "책상", "수납", "소파", "의자", "테이블", "조명", "장식", "기타"
    '''
    
    image_bytes = image.file.read()
    gemini_result = gemini_generate(prompt, image_bytes)

    return {"result": gemini_result}
