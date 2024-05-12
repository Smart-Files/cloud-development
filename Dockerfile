# The builder image, used to build the virtual environment
FROM python:3.11-bookworm AS builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    zlib1g-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libpq-dev \
    libgit2-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Python package installations
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app
COPY pyproject.toml /app/

# Install Python dependencies using Poetry
RUN pip install poetry && \
    poetry install --no-root && \
    rm -rf $POETRY_CACHE_DIR /root/.cache/pip

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app
COPY pyproject.toml /app/

RUN pip install fastapi langchain

COPY ./requirements.txt /app/requirements.txt

# Install runtime Python dependencies and remove caches immediately
RUN pip install -r requirements.txt && \
    rm -rf /root/.cache/pip

# Install runtime system dependencies and clean up in one step
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gdal-bin \
    curl \
    pandoc \
    imagemagick \
    libmagickwand-dev \
    poppler-utils \
    fuse \
    libfuse2 \
    sqlite3 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN curl -o /usr/bin/magick https://imagemagick.org/archive/binaries/magick && \
    chmod +x /usr/bin/magick

RUN pip install pysqlite3-binary \
    chromadb \
    langchain_openai

# Copy essential binaries and libraries from the builder stage
COPY --from=builder /usr/local /usr/local

# Set PATH to include the virtual environment's binary directory
ENV PATH="/app/.venv/bin:$PATH"

# Copy virtual environment including Streamlit
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY ./main.py /app/main.py
RUN mkdir /app/llm_docs /app/agent_tools /app/working_dir /app/fileprocessing
COPY ./fileprocessing/*.py /app/fileprocessing/
COPY ./fileprocessing/.env /app/fileprocessing/
RUN mkdir /app/fileprocessing/llm_docs
COPY ./fileprocessing/llm_docs/* /app/fileprocessing/llm_docs/
COPY ./fileprocessing/agent_tools/* /app/fileprocessing/agent_tools/

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# uvicorn main:app --host 0.0.0.0 --port 8080
