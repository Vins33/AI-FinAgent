# src/services/vector_store.py
"""Qdrant vector store service."""

from qdrant_client import QdrantClient, models

from src.core.config import settings


class VectorStoreService:
    """Service for interacting with Qdrant vector database."""

    COLLECTION_NAME = "instagram_content_kb"
    VECTOR_SIZE = 768  # nomic-embed-text dimension

    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
        )
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize collection if it doesn't exist."""
        try:
            self.client.get_collection(collection_name=self.COLLECTION_NAME)
            print(f"-> Qdrant: Found collection '{self.COLLECTION_NAME}'")
        except Exception:
            print(f"-> Qdrant: Creating collection '{self.COLLECTION_NAME}'...")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=self.VECTOR_SIZE, distance=models.Distance.COSINE
                ),
            )

    async def add_context(
        self, question_id: int, embedding: list[float], text: str
    ):
        """Add a vectorized context to the collection."""
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=question_id, vector=embedding, payload={"text": text}
                )
            ],
        )

    async def search(self, query_embedding: list[float], limit: int = 1) -> str:
        """Search for relevant contexts in the collection."""
        hits = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit,
        )
        if hits:
            return hits[0].payload.get("text", "")
        return "No relevant context found."
