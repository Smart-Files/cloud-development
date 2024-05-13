# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Install Python and system dependencies
RUN pip install --no-cache-dir pysqlite3-binary fastapi langchain chromadb langchain_openai firebase-admin && \
    apt-get update && apt-get install -y ffmpeg gdal-bin curl pandoc imagemagick libmagickwand-dev poppler-utils fuse libfuse2 sqlite3 --no-install-recommends && \
    curl -o /usr/bin/magick https://imagemagick.org/archive/binaries/magick && \
    chmod +x /usr/bin/magick && \
    curl -sSLf "$(curl -sSLf https://api.github.com/repos/tomwright/dasel/releases/latest | grep browser_download_url | grep linux_amd64 | grep -v .gz | cut -d\" -f 4)" -L -o /usr/bin/dasel && \
    chmod +x /usr/bin/dasel && \
    rm -rf /var/lib/apt/lists/* /root/.cache

EXPOSE 8080


# Copy necessary project files
COPY . .


# Remove unnecessary files and folders
RUN rm -rf test_cases

RUN pip install -r requirements.txt

RUN pip install uvicorn

COPY ./run.sh .

CMD ["./run.sh"]
