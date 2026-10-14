def rerank(candidates: list, query: str = "", decision_provider = None, top_n: int = 10) -> list:
    if not decision_provider or not candidates:
        return candidates
    
    scored_candidates = []
    for chunk, _ in candidates[:top_n]:
        score = decision_provider.relevance(query, chunk.text)
        scored_candidates.append((chunk, score))
        
    return sorted(scored_candidates, key=lambda x: x[1], reverse=True)
