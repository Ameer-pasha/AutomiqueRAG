from typing import Protocol

from src.core.ingestion.metadata import Chunk


class LLMProvider(Protocol):
    async def generate(self, question: str, context: list[Chunk]) -> str: ...
