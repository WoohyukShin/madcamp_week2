import sqlite3
from app.db.init_db import init_db
from app.db.db import Base, engine
from fastapi import Request
from fastapi import FastAPI
from app.routers import auth, user, feed, comment
from app.init_dummy_data import init_dummy_data
from starlette.responses import Response

init_db()
conn = sqlite3.connect("local.db")
cursor = conn.cursor()

app = FastAPI()
app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(user.router)
app.include_router(comment.router)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    init_dummy_data()


@app.middleware("http")
async def log_full_request(request: Request, call_next):
    print("====== INCOMING REQUEST ======")
    for k, v in request.headers.items():
        print(f"{k}: {v}")

    body = await request.body()
    content_type = request.headers.get("content-type", "")

    print("======== REQUEST BODY ========")

    if "application/json" in content_type or "text/" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            print(body.decode("utf-8", errors="replace"))
        except Exception as e:
            print(f"[디코딩 실패] {e}")

    elif "multipart/form-data" in content_type:
        try:
            async def receive():
                return {"type": "http.request", "body": body}

            request_for_form = Request(request.scope, receive=receive)

            form: FormData = await request_for_form.form()
            for key, value in form.multi_items():
                if hasattr(value, "filename"):
                    print(f"{key}: [파일 생략: {value.filename}]")
                else:
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"[multipart/form-data 파싱 실패] {e}")

    else:
        print(f"[Binary or unknown content-type: {content_type}] 생략")

    # 요청을 다시 살릴 수 있게 재주입
    async def receive():
        return {"type": "http.request", "body": body}

    # 응답 받기
    response = await call_next(Request(request.scope, receive=receive))

    # 응답 내용을 복사해서 출력
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    print("======= RESPONSE BODY ========")
    try:
        decoded = response_body.decode("utf-8")
        print(decoded)
    except Exception as e:
        print(f"[RESPONSE 디코딩 실패] {e}")
    print("==============================")

    return Response (
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )