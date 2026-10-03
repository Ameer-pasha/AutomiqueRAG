from dataclasses import dataclass, field


@dataclass(slots=True)
class Chunk:
    id: str
    parent_id: str
    document_id: str
    tenant_id: str
    text: str
    parent_text: str
    page: int
    section_path: str = "Document"
    metadata: dict[str, str | int | float] = field(default_factory=dict)
