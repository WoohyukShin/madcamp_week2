import app.models
from app.db.database import engine
from app.db.base import Base

def init_db():
    Base.metadata.create_all(bind=engine)