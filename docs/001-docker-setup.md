# 001 — Docker Setup

## Overview

Each component of PintMe has its own `Dockerfile`, and a `docker-compose.yml` at the repo root orchestrates the server components.

## Components

| Component | Type | Port | Build context |
|---|---|---|---|
| `embedding_server` | Server | 8100 | `./embedding_server` |
| `search_api` | Server | 8200 | repo root |
| `gui` | Server | 8501 | `./gui` |
| `indexer` | CLI (one-shot) | — | repo root |
| `rag` | CLI (one-shot) | — | repo root |

`search_api`, `indexer`, and `rag` use the repo root as build context because they import from parent-level modules (`models.py`, `indexer/`, `rag/`).

## Shared Volumes

- `db_data` — SQLite database (`pintme.db`)
- `chroma_data` — ChromaDB persist directory
- `${IMAGES_DIR:-./test_images}` bind-mounted at `/images` — image files accessible to both `indexer` and `search_api`

## CLI Tools

`indexer` and `rag` are placed under the `tools` profile so they are not started by `docker compose up`. Run them on demand:

```bash
docker compose run --rm indexer
docker compose run --rm rag
```

## Important

When running with Docker, `config.json` must point to `/images` (the container mount) rather than a host-absolute path:

```json
{ "explore": ["/images"] }
```
