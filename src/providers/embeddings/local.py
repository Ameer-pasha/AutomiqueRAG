import hashlib
import math
import re

from src.providers.embeddings.base import EmbeddingProvider

TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic development provider; replace with BGE-M3 in production."""

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimension
            for token in TOKEN_RE.findall(text.lower()):
                digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
                vector[int.from_bytes(digest[:4], "big") % self.dimension] += 1.0 if digest[4] % 2 else -1.0
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            result.append([value / norm for value in vector])
        return result
