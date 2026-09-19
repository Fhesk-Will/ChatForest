import json
from pathlib import Path
from datetime import datetime, timezone

from .base import StorageBackend


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_MODELS_CONFIG = {
    "providers": [
        {
            "id": "aliyun_qwen",
            "name": "阿里百炼",
            "type": "openai_compat",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long"],
        },
        {
            "id": "mimo_sub",
            "name": "MiMo (订阅版)",
            "type": "openai_compat",
            "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
            "api_key": "",
            "models": ["MiMo-7B-RL"],
        },
        {
            "id": "mimo_free",
            "name": "MiMo (非订阅版)",
            "type": "openai_compat",
            "base_url": "https://api.xiaomimimo.com/v1",
            "api_key": "",
            "models": ["MiMo-7B-RL"],
        },
    ],
    "default_model": {"provider_id": "aliyun_qwen", "model": "qwen-plus"},
}


class JsonStorage(StorageBackend):
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.index_file = data_dir / "index.json"
        self.models_file = data_dir / "models.json"
        self._ensure_index()

    def _ensure_index(self):
        if not self.index_file.exists():
            self._write_json(self.index_file, {"canvases": []})

    def _read_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _canvas_path(self, canvas_id: str) -> Path:
        return self.data_dir / f"canvas_{canvas_id}.json"

    async def list_canvases(self) -> list[dict]:
        index = self._read_json(self.index_file)
        return index.get("canvases", [])

    async def get_canvas(self, canvas_id: str) -> dict | None:
        path = self._canvas_path(canvas_id)
        if not path.exists():
            return None
        return self._read_json(path)

    async def save_canvas(self, canvas: dict) -> dict:
        canvas["updated_at"] = _now()
        self._write_json(self._canvas_path(canvas["id"]), canvas)

        index = self._read_json(self.index_file)
        canvases = index.get("canvases", [])
        entry = {"id": canvas["id"], "title": canvas.get("title", "未命名画布"), "updated_at": canvas["updated_at"]}
        existing = next((i for i, c in enumerate(canvases) if c["id"] == canvas["id"]), None)
        if existing is not None:
            canvases[existing] = entry
        else:
            canvases.insert(0, entry)
        self._write_json(self.index_file, {"canvases": canvases})
        return canvas

    async def delete_canvas(self, canvas_id: str) -> None:
        path = self._canvas_path(canvas_id)
        if path.exists():
            path.unlink()
        index = self._read_json(self.index_file)
        index["canvases"] = [c for c in index.get("canvases", []) if c["id"] != canvas_id]
        self._write_json(self.index_file, index)

    async def get_models_config(self) -> dict:
        if not self.models_file.exists():
            return DEFAULT_MODELS_CONFIG
        return self._read_json(self.models_file)

    async def save_models_config(self, config: dict) -> None:
        self._write_json(self.models_file, config)
