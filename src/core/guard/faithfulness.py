def verify_faithfulness(answer: str, context: str, decision_provider=None, threshold: float = 0.5) -> bool:
    if not decision_provider:
        return True
    return decision_provider.faithfulness(answer, context) >= threshold

def verify_citations(answer: str, citations: list, decision_provider=None, threshold: float = 0.5) -> list:
    if not decision_provider:
        return citations
    valid_citations = []
    for citation in citations:
        source_text = citation.text if hasattr(citation, "text") else str(citation)
        if decision_provider.citation_support(answer, source_text) >= threshold:
            valid_citations.append(citation)
    return valid_citations
