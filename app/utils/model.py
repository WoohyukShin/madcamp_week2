import os
import json
import redis
import requests
from fastapi import HTTPException
from fastapi import UploadFile

r = redis.Redis.from_url(os.getenv("REDIS_URL"))

def get_image_embedding(image):
    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")

    image.file.seek(0)
    try:
        files = {"image": (image.filename, image.file, image.content_type)}
        response = requests.post(f"{colab_url}/embed/image", files=files)
        response.raise_for_status()
        embedding = response.json()["embedding"]
        return embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch embedding from Colab: {e}")

def get_text_embedding(text):
    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")

    try:
        response = requests.post(f"{colab_url}/embed/text", data={"text": text})
        response.raise_for_status()
        embedding = response.json()["embedding"]
        return embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch embedding from Colab: {e}")

def gemini_generate(prompt: str, img_bytes: bytes) -> str:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
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
