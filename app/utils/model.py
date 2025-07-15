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

def get_text_embedding_with_rgb(text, r, g, b):
    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")

    try:
        response = requests.post(
            f"{colab_url}/embed/text",
            data={"text": text, "r": r, "g": g, "b": b}
        )
        response.raise_for_status()
        data = response.json()
        embedding = data["embedding"]
        color = data["color"]
        return embedding, color
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch embedding from Colab: {e}")
    
def analyze_bad_objects_with_text(image: UploadFile, prompt: str) -> list[str]:
    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")
    image.file.seek(0)
    
    try:
        files = {
            "image": (image.filename, image.file, image.content_type)
        }
        data = {
            "prompt": prompt
        }
        response = requests.post(
            f"{colab_url}/analyze/text",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()["bad_objects"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze image in Colab: {e}")

def analyze_bad_objects_with_image(image: UploadFile, embedding: list[float]) -> list[str]:
    colab_url = r.get("COLAB_SERVER_URL")
    if not colab_url:
        raise HTTPException(status_code=500, detail="Colab URL is not set")
    colab_url = colab_url.decode("utf-8")
    image.file.seek(0)

    files = {
        "image": (image.filename, image.file, image.content_type)
    }
    data = {
        "embedding": json.dumps(embedding)
    }
    try:
        response = requests.post(
            f"{colab_url}/analyze/image",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()["bad_objects"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze image in Colab: {e}")