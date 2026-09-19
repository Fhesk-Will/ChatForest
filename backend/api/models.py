from fastapi import APIRouter

from storage import JsonStorage
from config import DATA_DIR

router = APIRouter()
storage = JsonStorage(DATA_DIR)


@router.get("")
async def get_models():
    return await storage.get_models_config()


@router.put("")
async def save_models(body: dict):
    await storage.save_models_config(body)
    return {"ok": True}
