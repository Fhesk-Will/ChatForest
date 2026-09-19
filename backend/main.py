import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import canvas_router, chat_router, models_router

app = FastAPI(title="ChatForest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(canvas_router, prefix="/api/canvases")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(models_router, prefix="/api/models")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# 挂载前端构建产物（必须在所有 API 路由之后）
# 打包模式下前端资源由 PyInstaller 打进包里（sys._MEIPASS 为解包目录）
if getattr(sys, "frozen", False):
    FRONTEND_DIST = Path(sys._MEIPASS) / "frontend_dist"
else:
    FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
