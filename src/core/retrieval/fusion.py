def reciprocal_rank_fusion(dense, lexical, k: int = 60):
    scores, chunks = {}, {}
    for result_set in (dense, lexical):
        for rank, (chunk, _) in enumerate(result_set, start=1):
            chunks[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1 / (k + rank)
    return sorted(((chunks[key], score) for key, score in scores.items()), key=lambda item: item[1], reverse=True)
