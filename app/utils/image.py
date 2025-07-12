import os
from uuid import uuid4
from fastapi import UploadFile
from urllib.parse import urlparse

def save_image(
    file: UploadFile,
    folder_name: str  # 예: "feeds", "users"
) -> str:
    base_folder = f"static/images/{folder_name}"
    base_url = f"https://madcampweek2-production.up.railway.app/static/images/{folder_name}"

    os.makedirs(base_folder, exist_ok=True)

    ext = file.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"
    filepath = os.path.join(base_folder, filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    return f"{base_url}/{filename}"

def delete_image(image_url: str, folder_name: str):
    parsed = urlparse(image_url)
    filename = os.path.basename(parsed.path)
    path = os.path.join("static", "images", folder_name, filename)

    if os.path.exists(path):
        os.remove(path)