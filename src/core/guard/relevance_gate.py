def has_relevant_context(dense_results, threshold: float, query: str = "", decision_provider = None, laya_threshold: float = 0.5) -> bool:
    if not dense_results:
        return False
    if decision_provider:
        # Check top result semantic relevance
        return decision_provider.relevance(query, dense_results[0][0].text) >= laya_threshold
    return dense_results[0][1] >= threshold
