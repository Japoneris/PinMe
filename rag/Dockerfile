# Build context: repo root (rag imports from indexer/db.py)
FROM python:3.12-slim
WORKDIR /app

COPY rag/requirements.txt rag/requirements.txt
RUN pip install --no-cache-dir -r rag/requirements.txt

# Copy only what rag needs
COPY models.py .
COPY indexer/ indexer/
COPY rag/ rag/

WORKDIR /app/rag
# Expects:
#   /data/pintme.db  — db volume (populated by indexer first)
#   /chromadb        — chroma volume
#   embedding_server reachable at http://embedding_server:8100
CMD ["python", "run.py", \
     "--db", "/data/pintme.db", \
     "--chroma-dir", "/chromadb", \
     "--server", "http://embedding_server:8100"]
