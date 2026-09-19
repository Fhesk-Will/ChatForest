from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

from storage import JsonStorage
from config import DATA_DIR
from core import get_provider

router = APIRouter()
storage = JsonStorage(DATA_DIR)


def _now():
    return datetime.now(timezone.utc).isoformat()


@router.get("")
async def list_canvases():
    return await storage.list_canvases()


@router.post("")
async def create_canvas(body: dict = None):
    canvas_id = str(uuid.uuid4())[:8]
    canvas = {
        "id": canvas_id,
        "title": (body or {}).get("title", "未命名画布"),
        "created_at": _now(),
        "updated_at": _now(),
        "cards": [],
        "edges": [],
    }
    return await storage.save_canvas(canvas)


@router.get("/{canvas_id}")
async def get_canvas(canvas_id: str):
    canvas = await storage.get_canvas(canvas_id)
    if canvas is None:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas


@router.put("/{canvas_id}")
async def save_canvas(canvas_id: str, body: dict):
    body["id"] = canvas_id
    return await storage.save_canvas(body)


@router.delete("/{canvas_id}")
async def delete_canvas(canvas_id: str):
    await storage.delete_canvas(canvas_id)
    return {"ok": True}


class SummarizeTitleRequest(BaseModel):
    user_message: str


@router.post("/{canvas_id}/summarize-title")
async def summarize_title(canvas_id: str, body: SummarizeTitleRequest):
    canvas = await storage.get_canvas(canvas_id)
    if canvas is None:
        raise HTTPException(status_code=404, detail="Canvas not found")

    models_config = await storage.get_models_config()
    provider_id = models_config["default_model"]["provider_id"]
    model = models_config["default_model"]["model"]
    provider_config = next(
        (p for p in models_config["providers"] if p["id"] == provider_id), None
    )
    if not provider_config or not provider_config.get("api_key"):
        return {"title": ""}

    provider = get_provider(provider_config)
    messages = [
        {
            "role": "user",
            "content": f"请用不超过10个字总结以下对话内容作为标题，只输出标题文字，不要标点符号：\n{body.user_message}",
        }
    ]

    title_parts = []
    async for token in provider.chat(messages, model, stream=False):
        title_parts.append(token)
    title = "".join(title_parts).strip()[:20]

    canvas["title"] = title
    await storage.save_canvas(canvas)
    return {"title": title}
