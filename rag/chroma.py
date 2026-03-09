"""ChromaDB client and collection setup."""
import chromadb


def get_client(persist_dir: str) -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=persist_dir)


def get_image_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    """Collection for DINOv2 image embeddings."""
    return client.get_or_create_collection(
        name="image_embeddings",
        metadata={"hnsw:space": "cosine"},
    )


def get_text_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    """Collection for MiniLM text embeddings (on captions)."""
    return client.get_or_create_collection(
        name="text_embeddings",
        metadata={"hnsw:space": "cosine"},
    )
