import time
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from config.settings import settings


class PineconeService:
    def __init__(self, dimension: int) -> None:
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is missing.")

        self.dimension = dimension
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self._ensure_index()
        self.index = self.client.Index(settings.pinecone_index_name)

    def _ensure_index(self) -> None:
        try:
            existing_names = self.client.list_indexes().names()

            if settings.pinecone_index_name not in existing_names:
                self.client.create_index(
                    name=settings.pinecone_index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=settings.pinecone_cloud,
                        region=settings.pinecone_region,
                    ),
                )
                self._wait_until_ready()

            description = self.client.describe_index(
                settings.pinecone_index_name
            )
            current_dimension = int(description.dimension)

            if current_dimension != self.dimension:
                raise ValueError(
                    "Pinecone index dimension mismatch. "
                    f"Index={current_dimension}, "
                    f"embedding model={self.dimension}. "
                    "Use a new index name or recreate the index."
                )
        except Exception as error:
            raise ConnectionError(
                f"Pinecone connection/index error: {error}"
            ) from error

    def _wait_until_ready(self, timeout_seconds: int = 120) -> None:
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            description = self.client.describe_index(
                settings.pinecone_index_name
            )
            status = description.status
            ready = (
                status.get("ready")
                if isinstance(status, dict)
                else getattr(status, "ready", False)
            )
            if ready:
                return
            time.sleep(2)

        raise TimeoutError(
            "Pinecone index was not ready within 120 seconds."
        )

    def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str,
        batch_size: int = 100,
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunk and embedding counts do not match."
            )

        vectors: list[dict[str, Any]] = []
        for chunk, embedding in zip(chunks, embeddings):
            vectors.append(
                {
                    "id": chunk["chunk_id"],
                    "values": embedding,
                    "metadata": {
                        "document_id": chunk["document_id"],
                        "document_name": chunk["document_name"],
                        "page_number": int(chunk["page_number"]),
                        "chunk_number": int(chunk["chunk_number"]),
                        "text": chunk["text"],
                        "ocr_used": bool(chunk["ocr_used"]),
                        "extraction_method": (
                            chunk["extraction_method"]
                        ),
                    },
                }
            )

        try:
            for start in range(0, len(vectors), batch_size):
                self.index.upsert(
                    vectors=vectors[start : start + batch_size],
                    namespace=namespace,
                )
        except Exception as error:
            raise ConnectionError(
                f"Could not upsert vectors to Pinecone: {error}"
            ) from error

        return len(vectors)

    def query(
        self,
        vector: list[float],
        top_k: int,
        namespace: str,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
                filter=metadata_filter,
            )
        except Exception as error:
            raise ConnectionError(
                f"Pinecone query failed: {error}"
            ) from error

        return [
            {
                "id": match.id,
                "score": float(match.score),
                "metadata": dict(match.metadata or {}),
            }
            for match in response.matches
        ]

    def delete_namespace(self, namespace: str) -> None:
        try:
            self.index.delete(
                delete_all=True,
                namespace=namespace,
            )
        except Exception as error:
            raise ConnectionError(
                f"Could not clear namespace: {error}"
            ) from error
