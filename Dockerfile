# Python 3.14 is pre-release; use 3.14-rc-slim if available, otherwise 3.13-slim.
# Check https://hub.docker.com/_/python/tags?name=3.14 at build time.
FROM python:3.13-slim

# Install system dependencies: pandoc for DOCX conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
        pandoc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what pip needs first (layer-cache friendly)
COPY pyproject.toml ./
COPY resume_helper/ ./resume_helper/
COPY shared/ ./shared/

# Install package with optional GUI extras
RUN pip install --no-cache-dir -e ".[gui]"

# users/ is NOT copied — it must be volume-mounted at runtime
# so that user data and outputs persist outside the container.

EXPOSE 7860

CMD ["resume-helper-app"]
