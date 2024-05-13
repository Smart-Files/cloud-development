# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

COPY pyproject.toml /app/

COPY ./requirements.txt /app/requirements.txt

# Install runtime Python dependencies and remove caches immediately
RUN pip install -r /app/requirements.txt && \
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

# Install Python dependencies
RUN pip install pysqlite3-binary \
    fastapi \
    langchain \
    chromadb \
    langchain_openai 

# Install Dasel 
RUN curl -sSLf "$(curl -sSLf https://api.github.com/repos/tomwright/dasel/releases/latest | grep browser_download_url | grep linux_amd64 | grep -v .gz | cut -d\" -f 4)" -L -o dasel
RUN chmod +x dasel
RUN mv ./dasel /usr/bin/dasel

# Install Firebase
RUN pip install --user firebase-admin

# WORKDIR /app

# Set PATH to include the virtual environment's binary directory

# Copy the application code
COPY ./main.py /app/main.py
COPY ./main.py /app/
COPY ./main.py /
COPY ./main.py /main.py
COPY ./main.py /app/fileprocessing/main.py
COPY ./main.py /app/fileprocessing/
RUN mkdir /app/working_dir /app/fileprocessing
COPY ./db /app/db
COPY ./fileprocessing/* /app/fileprocessing/
RUN mkdir /app/fileprocessing/llm_docs
COPY ./fileprocessing/llm_docs/* /app/fileprocessing/llm_docs/
COPY ./fileprocessing/agent_tools/* /app/fileprocessing/agent_tools/

RUN touch /app/__init__.py



EXPOSE 8080
# WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# uvicorn app.main:app --host 0.0.0.0 --port 8080
