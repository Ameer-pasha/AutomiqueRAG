import re
from collections import Counter

from src.core.retrieval.fusion import reciprocal_rank_fusion


def hybrid_search(store, query: str, vector: list[float], tenant_id: str, document_ids: set[str] | None, limit: int):
    dense = store.search(vector, tenant_id, document_ids, limit)
    terms = re.findall(r"[\w-]+", query.lower())
    def lexical_score(item):
        counts = Counter(re.findall(r"[\w-]+", item[0].text.lower()))
        return sum(counts[term] for term in terms) / max(sum(counts.values()), 1)
    return dense, reciprocal_rank_fusion(dense, sorted(dense, key=lexical_score, reverse=True))
