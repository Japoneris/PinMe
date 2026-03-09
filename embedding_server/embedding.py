"""Embedding helpers: model loading, image/text utilities, and inference."""
import base64
import io
import json
import os
import struct
from pathlib import Path
from typing import Any, Optional

import requests
import torch
from PIL import Image


# ---------------------------------------------------------------------------
# Device configuration
# ---------------------------------------------------------------------------

def get_device() -> str:
    """Resolve device from DEVICE env var (auto/cpu/cuda/gpu)."""
    env = os.environ.get("DEVICE", "auto").lower()
    if env == "cpu":
        return "cpu"
    if env in ("cuda", "gpu"):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but not available")
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


DEVICE = get_device()
print("DEVICE:", DEVICE)


# ---------------------------------------------------------------------------
# Image loading
# ---------------------------------------------------------------------------

def load_image(input_data: str) -> Image.Image:
    """Load an image from a URL, base64 data URL, raw base64, or local path."""
    if input_data.startswith(("http://", "https://")):
        response = requests.get(input_data, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    if input_data.startswith("data:image"):
        _header, data = input_data.split(",", 1)
        return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
    # local file path — wrap in try/except to handle strings too long for the OS
    try:
        path = Path(input_data)
        if path.exists():
            return Image.open(path).convert("RGB")
    except OSError:
        pass
    # fallback: raw base64
    return Image.open(io.BytesIO(base64.b64decode(input_data))).convert("RGB")


# ---------------------------------------------------------------------------
# Model card
# ---------------------------------------------------------------------------

class ModelCard:
    """A model described by a JSON file in models/."""

    def __init__(self, cfg: dict):
        self.id: str = cfg["id"]
        self.name: str = cfg["name"]
        self.hf_model: str = cfg["hf_model"]
        self.task: str = cfg["task"]           # "image-embedding" | "text-embedding"
        self.description: str = cfg.get("description", "")
        self.embedding_dim: Optional[int] = cfg.get("embedding_dim")
        self.size_mb: Optional[int] = cfg.get("size_mb")

        # runtime
        self.model: Any = None
        self.processor: Any = None  # ImageProcessor or Tokenizer

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "object": "model",
            "created": 0,
            "owned_by": "local",
            "name": self.name,
            "task": self.task,
            "description": self.description,
            "size_mb": self.size_mb,
            "loaded": self.loaded,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ModelRegistry:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models: dict[str, ModelCard] = {}

    def scan(self) -> None:
        self.models.clear()
        if not self.models_dir.exists():
            return
        for p in self.models_dir.glob("*.json"):
            try:
                with open(p) as f:
                    card = ModelCard(json.load(f))
                self.models[card.id] = card
            except Exception as e:
                print(f"Warning: skipping {p}: {e}")

    def get(self, model_id: str) -> Optional[ModelCard]:
        return self.models.get(model_id)

    def load(self, model_id: str) -> ModelCard:
        card = self.get(model_id)
        if card is None:
            raise ValueError(f"Model not found: {model_id}")
        if card.loaded:
            return card
        if card.task == "text-embedding":
            card.model, card.processor = _load_text_model(card)
        elif card.task == "image-to-text":
            card.model, card.processor = _load_vl_model(card)
        else:
            card.model, card.processor = _load_vision_model(card)
        return card

    def unload_all(self) -> None:
        for card in self.models.values():
            card.model = None
            card.processor = None


registry = ModelRegistry()


# ---------------------------------------------------------------------------
# Model loaders
# ---------------------------------------------------------------------------

def _load_vision_model(card: ModelCard):
    from transformers import AutoImageProcessor, AutoModel
    processor = AutoImageProcessor.from_pretrained(card.hf_model)
    model = AutoModel.from_pretrained(card.hf_model).to(DEVICE)
    return model, processor


def _load_vl_model(card: ModelCard):
    from transformers import AutoProcessor, AutoModelForImageTextToText

    kwargs = {}
    if DEVICE == "cuda":
        kwargs["device_map"] = "auto"
        kwargs["torch_dtype"] = torch.float16

    model = AutoModelForImageTextToText.from_pretrained(card.hf_model, **kwargs)
    if DEVICE != "cuda":
        model = model.to(DEVICE)

    processor = AutoProcessor.from_pretrained(card.hf_model)
    return model, processor


def _load_text_model(card: ModelCard):
    from transformers import AutoTokenizer, AutoModel
    tokenizer = AutoTokenizer.from_pretrained(card.hf_model)
    model = AutoModel.from_pretrained(card.hf_model).to(DEVICE)
    return model, tokenizer


# ---------------------------------------------------------------------------
# Encoding helper
# ---------------------------------------------------------------------------

def encode_embedding(embedding: list[float], fmt: str) -> list[float] | str:
    if fmt == "base64":
        packed = struct.pack(f"{len(embedding)}f", *embedding)
        return base64.b64encode(packed).decode("utf-8")
    return embedding


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def compute_image_embedding(card: ModelCard, image: Image.Image, encoding_format: str = "float") -> dict:
    """Run a vision model on a single image."""
    if not card.loaded:
        raise RuntimeError(f"Model {card.id} is not loaded")

    inputs = card.processor(images=image, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = card.model(**inputs)

    last_hidden = outputs.last_hidden_state          # (1, seq, dim)
    cls_embedding = last_hidden[0, 0, :].tolist()    # CLS token

    return {
        "embedding": encode_embedding(cls_embedding, encoding_format),
        "tokens": last_hidden.shape[1],
    }


def compute_caption(card: ModelCard, image: Image.Image, prompt: str = "Describe this image.", max_new_tokens: int = 256) -> dict:
    """Run a vision-language model to generate a caption for an image."""
    if not card.loaded:
        raise RuntimeError(f"Model {card.id} is not loaded")

    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    inputs = card.processor.apply_chat_template(
        conversation,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
        tokenize=True,
    ).to(card.model.device)

    with torch.no_grad():
        outputs = card.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            do_sample=True,
        )

    input_len = inputs["input_ids"].shape[1]
    generated_ids = outputs[:, input_len:]
    text = card.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return {"text": text, "tokens": generated_ids.shape[1]}


def compute_text_embedding(card: ModelCard, text: str, encoding_format: str = "float") -> dict:
    """Run a text model on a single string (mean pooling)."""
    if not card.loaded:
        raise RuntimeError(f"Model {card.id} is not loaded")

    inputs = card.processor(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = card.model(**inputs)

    # mean pooling over token dimension, masked by attention
    last_hidden = outputs.last_hidden_state          # (1, seq, dim)
    attention_mask = inputs["attention_mask"]        # (1, seq)
    mask = attention_mask.unsqueeze(-1).float()
    pooled = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1)
    embedding = pooled[0].tolist()

    return {
        "embedding": encode_embedding(embedding, encoding_format),
        "tokens": last_hidden.shape[1],
    }
