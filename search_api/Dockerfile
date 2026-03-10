# Build context: repo root (search_api imports from indexer/, rag/, models.py)
FROM python:3.12-slim
WORKDIR /app

# Install dependencies from both search_api and rag (needed for chroma imports)
COPY search_api/requirements.txt search_api/requirements.txt
COPY rag/requirements.txt rag/requirements.txt
RUN pip install --no-cache-dir \
    -r search_api/requirements.txt \
    -r rag/requirements.txt

# Copy only the modules that search_api depends on
COPY models.py .
COPY indexer/ indexer/
COPY rag/ rag/
COPY search_api/ search_api/

WORKDIR /app/search_api
EXPOSE 8200
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8200"]
