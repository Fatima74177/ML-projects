# Build context is the REPO ROOT (see docker-compose.yml: build.context: .)
# so that backend/, scripts/, and data/ can all be copied into the image at
# sibling paths -- this lets the seed script's relative "../data" path work
# identically in Docker and on the host.
FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/src/ ./src/
COPY frontend/index.html frontend/vite.config.ts frontend/tsconfig.json ./
COPY frontend/postcss.config.js frontend/tailwind.config.js ./
RUN npm run build

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /eef

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY scripts/ scripts/
COPY data/ data/
COPY --from=frontend-build /frontend/dist/ frontend/dist/

WORKDIR /eef/backend
RUN mkdir -p /eef/backend/uploads
RUN chmod +x docker-entrypoint.sh

ENV PYTHONPATH=/eef/backend
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=25s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
