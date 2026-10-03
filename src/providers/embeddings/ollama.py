import httpx


class OllamaEmbeddingProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(f"{self.base_url}/api/embed", json={"model": self.model, "input": texts}, timeout=90)
        response.raise_for_status()
        return response.json()["embeddings"]
