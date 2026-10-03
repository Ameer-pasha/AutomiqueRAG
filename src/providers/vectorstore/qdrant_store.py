class QdrantStore:
    """Production adapter boundary; wire qdrant-client here."""

    def __init__(self, url: str) -> None:
        self.url = url
