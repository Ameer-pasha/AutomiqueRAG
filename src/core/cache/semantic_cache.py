class SemanticCache:
    def __init__(self) -> None:
        self.items = []

    def get(self, query_vector, tenant_id, threshold):
        for vector, tenant, value in self.items:
            if tenant == tenant_id and sum(a * b for a, b in zip(vector, query_vector, strict=True)) >= threshold:
                return value
        return None

    def put(self, query_vector, tenant_id, value) -> None:
        self.items.append((query_vector, tenant_id, value))
        self.items = self.items[-100:]
