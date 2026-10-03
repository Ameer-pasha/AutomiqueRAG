class FaissStore:
    """Adapter placeholder for importable FAISS indexes."""

    def import_index(self, source: str) -> None:
        raise NotImplementedError("FAISS import requires the source text and embedding metadata validation.")
