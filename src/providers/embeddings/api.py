from src.providers.embeddings.base import EmbeddingProvider


class APIEmbeddingProvider(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Configure a hosted embedding adapter for this provider.")
