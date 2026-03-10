# Build context: repo root (indexer imports models.py from parent)
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir sqlalchemy pillow

# Copy only what indexer needs
COPY models.py .
COPY indexer/ indexer/

WORKDIR /app/indexer
# Expects:
#   /data/pintme.db   — db volume
#   /images           — bind-mounted image directory
#   /config/config.json — bind-mounted config (explore paths must use /images)
CMD ["python", "run.py", "--db", "/data/pintme.db", "--config", "/config/config.json"]
