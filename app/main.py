from fastapi import FastAPI

app = FastAPI()
Base.metadata.create_all(bind=engine)

app = FastAPI()
# app.include_router()
