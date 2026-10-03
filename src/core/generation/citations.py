from src.schemas.chat import Citation


def citations_for(chunks):
    return [Citation(document_id=chunk.document_id, filename=str(chunk.metadata["filename"]), page=chunk.page, chunk_id=chunk.id) for chunk in chunks]
