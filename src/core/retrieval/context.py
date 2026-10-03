def build_context(results, limit: int):
    seen, context = set(), []
    for chunk, _ in results:
        if chunk.parent_id not in seen:
            seen.add(chunk.parent_id)
            context.append(chunk)
        if len(context) >= limit:
            break
    return context
