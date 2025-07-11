from fastapi import FastAPI
from app.db.init_db import init_db
from app.routers import auth

app = FastAPI()
app.include_router(auth.router)

init_db()