from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_sessions import router as sessions_router
from app.api.routes_steps import router as steps_router
from app.api.routes_export import router as export_router
from app.api.routes_chat import router as chat_router

app = FastAPI(title="Diagram Agent")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(steps_router)
app.include_router(export_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"ok": True}
