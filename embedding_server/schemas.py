"""Pydantic schemas for API requests and responses."""
from typing import Optional
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Model information (OpenAI compatible)."""
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "local"
    name: Optional[str] = None
    task: Optional[str] = None
    description: Optional[str] = None
    size_mb: Optional[int] = None
    loaded: bool = False


class ModelListResponse(BaseModel):
    """Response for /v1/models."""
    object: str = "list"
    data: list[ModelInfo]


class EmbeddingRequest(BaseModel):
    """Request for /v1/embeddings — image inputs (URL, base64, or local path)."""
    model: str
    input: str | list[str]
    encoding_format: str = "float"  # "float" or "base64"


class TextEmbeddingRequest(BaseModel):
    """Request for /v1/text-embeddings — plain text inputs."""
    model: str
    input: str | list[str]
    encoding_format: str = "float"  # "float" or "base64"


class CaptionRequest(BaseModel):
    """Request for /v1/captions — generate text from image(s)."""
    model: str
    input: str | list[str]          # image: URL, local path, data URL, or raw base64
    prompt: str = "Describe this image."
    max_new_tokens: int = 256


class CaptionData(BaseModel):
    """Single caption result."""
    text: str
    index: int = 0


class CaptionResponse(BaseModel):
    """Response for /v1/captions."""
    object: str = "list"
    data: list[CaptionData]
    model: str
    usage: dict


class EmbeddingData(BaseModel):
    """Single embedding result."""
    object: str = "embedding"
    embedding: list[float] | str
    index: int = 0


class EmbeddingResponse(BaseModel):
    """Response for embedding endpoints."""
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: dict
