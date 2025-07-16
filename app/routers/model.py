import os
from typing import Dict, List
from fastapi import APIRouter, Form, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.db import get_db
from dotenv import load_dotenv
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.product import build_product_summary_response
import google.generativeai as genai
from PIL import Image
import tempfile

# load_dotenv()
# key=os.getenv("GEMINI_API_KEY")
def gemini_generate(prompt: str, img_bytes: bytes) -> str:
    genai.configure(api_key="AIzaSyAjG2e0ECRcU02r3EP_64XtAq6RqtpPB24")
    model = genai.GenerativeModel("gemini-1.5-flash")
    image_part = {
        "mime_type": "image/jpeg",
        "data": img_bytes
    }

    try:
        response = model.generate_content([prompt, image_part])
        return response.text.strip()
    except Exception as e:
        raise Exception(f"Gemini generate_content 오류: {str(e)}")


router = APIRouter(prefix="/model")

@router.post("/recommend/text")
def get_recommendation_from_text(
    text: str = Form(...),
    r: str = Form(...),
    g: str = Form(...),
    b: str = Form(...),
    image: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    print("hello world?????")
    prompt = f'''
        나는 지금 r={r},g={g},b={b} color 톤의 {text} 스타일로 내 방을 꾸미고 싶어. 참고를 위해 내 방 사진도 함께 첨부할게.
        r, g, b 값을 숫자로 다시 출력해 주지 말고, 자연어 Color로 바꿔서 얘기해 줘.

        내 방 사진을 분석해서, 아래에 명시된 카테고리 중 내 스타일과 톤에 어울리지 않는 가구들을 찾아줘. 각 가구가 어울리지 않는 이유도 간단히 설명해 줘.

        출력 형식은 반드시 아래와 같이 JSON으로 파싱 가능한 string으로 출력해야 해.

        "의자": "현재 의자는 너무 화려해서 모던 스타일과 조화롭지 않습니다.",
        "수납": "서랍의 색상이 전체 톤과 맞지 않아 이질감이 듭니다.",
        "기타": "전체적으로 고전적인 느낌의 가구들이 섞여 있어 스타일이 혼재되어 보입니다."

        사용 가능한 카테고리는 다음으로 제한해:
        "침대", "책상", "수납", "소파", "의자", "테이블", "조명", "장식", "기타"
    '''
    
    image_bytes = image.file.read()
    gemini_result = gemini_generate(prompt, image_bytes)
    print(gemini_result)

    return gemini_result