from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    async def list_canvases(self) -> list[dict]: ...

    @abstractmethod
    async def get_canvas(self, canvas_id: str) -> dict | None: ...

    @abstractmethod
    async def save_canvas(self, canvas: dict) -> dict: ...

    @abstractmethod
    async def delete_canvas(self, canvas_id: str) -> None: ...

    @abstractmethod
    async def get_models_config(self) -> dict: ...

    @abstractmethod
    async def save_models_config(self, config: dict) -> None: ...
