def has_relevant_context(dense_results, threshold: float) -> bool:
    return bool(dense_results) and dense_results[0][1] >= threshold
