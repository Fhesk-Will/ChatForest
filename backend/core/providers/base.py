from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: str,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]: ...
