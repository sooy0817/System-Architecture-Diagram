from fastapi import FastAPI
from app.api.routes_sessions import router as sessions_router
from app.api.routes_steps import router as steps_router
from app.api.routes_export import router as export_router

app = FastAPI(title="Diagram Agent")

app.include_router(sessions_router)
app.include_router(steps_router)
app.include_router(export_router)


@app.get("/health")
def health():
    return {"ok": True}
