from typing import Any

from core.embedding_service import EmbeddingService
from core.pinecone_service import PineconeService


class Retriever:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        pinecone_service: PineconeService,
    ) -> None:
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service

    def retrieve(
        self,
        query: str,
        namespace: str,
        top_k: int,
        similarity_threshold: float,
        document_names: list[str] | None = None,
        page_number: int | None = None,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("Query cannot be empty.")

        metadata_filter: dict[str, Any] = {}

        if document_names:
            metadata_filter["document_name"] = {
                "$in": document_names
            }

        if page_number is not None:
            metadata_filter["page_number"] = {
                "$eq": int(page_number)
            }

        query_vector = self.embedding_service.embed_query(query)
        matches = self.pinecone_service.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            metadata_filter=metadata_filter or None,
        )

        return [
            match
            for match in matches
            if match["score"] >= similarity_threshold
        ]


def calculate_retrieval_confidence(
    sources: list[dict[str, Any]],
) -> float:
    """Similarity-derived indicator, not a calibrated probability."""
    if not sources:
        return 0.0

    scores = [
        max(0.0, min(1.0, float(source["score"])))
        for source in sources
    ]
    top_score = max(scores)
    average_score = sum(scores) / len(scores)

    return max(
        0.0,
        min(1.0, (0.65 * top_score) + (0.35 * average_score)),
    )
