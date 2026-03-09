# Embedding Server

FastAPI microserver exposing three inference endpoints used by the rest of the PintMe stack.

## Models

| Model | Task | Endpoint |
|---|---|---|
| `dinov2-small` | Image → vector (dim 384) | `POST /v1/embeddings` |
| `minilm-v6` | Text → vector (dim 384) | `POST /v1/text-embeddings` |
| `lfm2-vl-450m` | Image → caption text | `POST /v1/captions` |

Models are described by JSON cards in `models/` and loaded at startup.

## Run

```bash
pip install -r requirements.txt
python run.py                        # default: 0.0.0.0:8100
python run.py --port 8100 --device cpu
python run.py --device cuda
```

## Endpoints

```bash
# List loaded models
GET /v1/models

# Image embedding (local path, URL, base64, or data URL)
POST /v1/embeddings
{"model": "dinov2-small", "input": "/path/to/image.jpg"}

# Text embedding
POST /v1/text-embeddings
{"model": "minilm-v6", "input": "a cat on a chair"}

# Image captioning
POST /v1/captions
{"model": "lfm2-vl-450m", "input": "/path/to/image.jpg", "prompt": "Describe this image."}
```

## Tests

```bash
pytest test_routes.py -v -s
```

Requires the server to be running on `localhost:8100` and test images to be present in `../test_images/`.
