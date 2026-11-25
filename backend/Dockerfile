FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# WeasyPrint needs Pango; Noto fonts cover Tamil and the rupee sign
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg62-turbo \
        fonts-noto-core fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN useradd -m app && mkdir -p /data/storage && chown -R app /data /app
USER app
ENV STORAGE_DIR=/data/storage
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m app.services.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
