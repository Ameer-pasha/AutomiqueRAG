from src.core.guard.relevance_gate import has_relevant_context
from src.core.retrieval.fusion import reciprocal_rank_fusion
from src.core.ingestion.metadata import Chunk


def test_rrf_combines_rankings():
    chunk = Chunk("one", "parent", "doc", "tenant", "text", "text", 1, metadata={"filename": "a.pdf"})
    assert reciprocal_rank_fusion([(chunk, 0.8)], [(chunk, 0.2)])[0][0].id == "one"


def test_relevance_gate_uses_dense_score():
    assert has_relevant_context([(object(), 0.2)], 0.12)
    assert not has_relevant_context([(object(), 0.1)], 0.12)
