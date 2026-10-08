FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Apply the latest security patches to the base image's system packages,
# and install Tesseract OCR for scanned PDFs and images
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade Python's packaging tools (fixes e.g. wheel CVE-2026-24049), install the app's packages,
# then remove pip: it is only needed at build time, and it bundles its own older copies of
# urllib3, msgpack and setuptools that Trivy flags.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

COPY . .

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
