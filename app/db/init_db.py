from app.models import *
from app.db.db import engine
from app.db.db import Base

def init_db():
    Base.metadata.create_all(bind=engine)