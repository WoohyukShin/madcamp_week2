from fastapi import FastAPI
from app.db.init_db import init_db
from app.routers import auth
from app.init_dummy_data import init_dummy_data

app = FastAPI()
app.include_router(auth.router)

init_db()

@app.on_event("startup")
def startup_event():
    init_dummy_data()