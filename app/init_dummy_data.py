from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.feed import Feed
from app.db.db import SessionLocal
from app.utils.auth import get_password_hash

def init_dummy_data():
    db: Session = SessionLocal()

    if db.query(User).first():
        print("Dummy data already exists.")
        db.close()
        return

    admin = User (
        email = "admin@example.com",
        name = "admin",
        imageURL = "",
        nickname = "admin",
        password = get_password_hash("abcd1234"),
        birthday = None,
        gender = "Male",
        auth_type = "email"
    )
    
    db.add(admin)
    db.commit()