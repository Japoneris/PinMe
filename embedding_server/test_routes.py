"""Tests for the embedding server routes."""
import random
from pathlib import Path

import pytest
import requests

BASE_URL = "http://localhost:8100"
IMAGES_DIR = Path(__file__).parent.parent / "test_images"

IMAGE_MODEL = "dinov2-small"
TEXT_MODEL = "minilm-v6"
CAPTION_MODEL = "lfm2-vl-450m"


def random_image() -> Path:
    images = list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))
    assert images, f"No images found in {IMAGES_DIR}"
    return random.choice(images)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /v1/models
# ---------------------------------------------------------------------------

def test_list_models():
    r = requests.get(f"{BASE_URL}/v1/models")
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "list"
    ids = [m["id"] for m in body["data"]]
    assert IMAGE_MODEL in ids
    assert TEXT_MODEL in ids
    assert CAPTION_MODEL in ids


# ---------------------------------------------------------------------------
# POST /v1/embeddings  (image)
# ---------------------------------------------------------------------------

def test_image_embedding_local_path():
    image = random_image()
    print(f"\n  Using image: {image.name}")
    r = requests.post(
        f"{BASE_URL}/v1/embeddings",
        json={"model": IMAGE_MODEL, "input": str(image)},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == IMAGE_MODEL
    assert len(body["data"]) == 1
    emb = body["data"][0]["embedding"]
    assert isinstance(emb, list)
    assert len(emb) == 384
    assert all(isinstance(v, float) for v in emb)
    print(f"  Embedding dim: {len(emb)}, elapsed: {body['usage']['elapsed_seconds']}s")


def test_image_embedding_wrong_model_task():
    """Text model should be rejected on /v1/embeddings."""
    image = random_image()
    r = requests.post(
        f"{BASE_URL}/v1/embeddings",
        json={"model": TEXT_MODEL, "input": str(image)},
    )
    assert r.status_code == 400


def test_image_embedding_unknown_model():
    r = requests.post(
        f"{BASE_URL}/v1/embeddings",
        json={"model": "does-not-exist", "input": "/tmp/fake.jpg"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /v1/text-embeddings  (text)
# ---------------------------------------------------------------------------

def test_text_embedding_single():
    r = requests.post(
        f"{BASE_URL}/v1/text-embeddings",
        json={"model": TEXT_MODEL, "input": "a cat sitting on a chair"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == TEXT_MODEL
    assert len(body["data"]) == 1
    emb = body["data"][0]["embedding"]
    assert isinstance(emb, list)
    assert len(emb) == 384
    print(f"\n  Text embedding dim: {len(emb)}, elapsed: {body['usage']['elapsed_seconds']}s")


def test_text_embedding_batch():
    texts = ["a red car", "a blue sky", "a forest at night"]
    r = requests.post(
        f"{BASE_URL}/v1/text-embeddings",
        json={"model": TEXT_MODEL, "input": texts},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["data"]) == len(texts)
    for i, item in enumerate(body["data"]):
        assert item["index"] == i
        assert len(item["embedding"]) == 384


def test_text_embedding_wrong_model_task():
    """Image model should be rejected on /v1/text-embeddings."""
    r = requests.post(
        f"{BASE_URL}/v1/text-embeddings",
        json={"model": IMAGE_MODEL, "input": "hello"},
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /v1/captions  (image-to-text)
# ---------------------------------------------------------------------------

def test_caption_default_prompt():
    image = random_image()
    print(f"\n  Using image: {image.name}")
    r = requests.post(
        f"{BASE_URL}/v1/captions",
        json={"model": CAPTION_MODEL, "input": str(image)},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == CAPTION_MODEL
    assert len(body["data"]) == 1
    text = body["data"][0]["text"]
    assert isinstance(text, str)
    assert len(text) > 0
    print(f"  Caption: {text!r}")
    print(f"  Elapsed: {body['usage']['elapsed_seconds']}s")


def test_caption_custom_prompt():
    image = random_image()
    r = requests.post(
        f"{BASE_URL}/v1/captions",
        json={"model": CAPTION_MODEL, "input": str(image), "prompt": "What objects are visible?"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    text = body["data"][0]["text"]
    assert isinstance(text, str)
    assert len(text) > 0
    print(f"\n  Caption (custom prompt): {text!r}")


def test_caption_wrong_model_task():
    """Embedding model should be rejected on /v1/captions."""
    image = random_image()
    r = requests.post(
        f"{BASE_URL}/v1/captions",
        json={"model": IMAGE_MODEL, "input": str(image)},
    )
    assert r.status_code == 400
