class OpenSearchStore:
    """Hybrid BM25/dense OpenSearch adapter boundary."""

    def __init__(self, url: str) -> None:
        self.url = url
