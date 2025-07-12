import os
import boto3
from uuid import uuid4
from fastapi import UploadFile
from urllib.parse import urlparse

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def save_image(file: UploadFile, folder_name: str) -> str:
    ext = file.filename.split(".")[-1]
    filename = f"{folder_name}/{uuid4().hex}.{ext}"

    s3.upload_fileobj(
        file.file,
        AWS_S3_BUCKET,
        filename,
        ExtraArgs={
            "ContentType": file.content_type,
            "ACL": "public-read"
        }
    )

    imageURL = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"
    return imageURL

def delete_image(image_url: str, folder_name: str):
    parsed = urlparse(image_url)
    filename = os.path.basename(parsed.path)
    key = f"{folder_name}/{filename}"

    s3.delete_object(Bucket=AWS_S3_BUCKET, Key=key)