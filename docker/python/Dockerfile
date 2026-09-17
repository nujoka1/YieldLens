FROM python:3.12.7-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt \
    && useradd --create-home --uid 10001 yieldlens

# Phase 1.5 is a development image: include the pinned test/coverage toolchain.
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir --requirement requirements-dev.txt

COPY --chown=yieldlens:yieldlens src ./src
USER yieldlens

CMD ["python", "-m", "yieldlens.runtime"]
