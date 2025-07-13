import redis
from fastapi import APIRouter, Request
import os

router = APIRouter()
r = redis.Redis.from_url(os.getenv("REDIS_URL"))

@router.post("/set_colab_url")
async def set_colab_url(req: Request):
    data = await req.json()
    colab_url = data.get("colab_url")
    r.set("COLAB_SERVER_URL", colab_url)
    print(f"new COLAB_SERVER_URL={colab_url}")
    return {"message": "colab_url saved"}