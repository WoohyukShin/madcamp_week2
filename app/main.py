from fastapi import FastAPI
from app.db.init_db import init_db
from app.routers import auth, user, feed, comment
from app.init_dummy_data import init_dummy_data

app = FastAPI()
app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(user.router)
app.include_router(comment.router)

init_db()

@app.on_event("startup")
def startup_event():
    init_dummy_data()