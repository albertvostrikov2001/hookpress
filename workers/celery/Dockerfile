FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY workers/celery/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY workers/celery/ .

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
