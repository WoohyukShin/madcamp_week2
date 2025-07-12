import os
import json
import redis
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List
from app.db.db import get_db
from app.models import *
from app.schemas import *
from app.utils.auth import get_current_user
from app.utils.image import save_image, delete_image

router = APIRouter(prefix="/user")


@router.post("/profile-image")
def update_profile_image(image: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):

    if user.imageURL:
        delete_image(user.imageURL, "users")

    imageURL = save_image(image, folder_name="users")
    user.imageURL = imageURL
    db.commit()

    return {"message": "Profile image updated", "imageURL": imageURL}

