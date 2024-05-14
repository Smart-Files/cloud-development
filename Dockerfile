FROM python:3.10-slim
# RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /cloud


# RUN apt update && apt install b÷ild-essential software-properties-common -y

# RUN add-apt-repository ppa:deadsnakes/ppa


# RUN apt-get update && apt-get install -y \
#     git \
#     libpython3.11-dev \
#     python3.11-dev \
#     python3.11-venv \
#     python3.11-distutils \
#     python3.11 \
#     python3.11-full \
#     python3-pip

# RUN ls -la /usr/bin
# RUN ls -la /usr/local/bin



RUN apt-get update && apt-get install -y software-properties-common \
    wget \
    curl \
    imagemagick \
    ffmpeg \
    gdal-bin \
    pandoc \
    libmagickwand-dev \
    poppler-utils \
    fuse \
    libfuse2 \
    sqlite3 \
    --no-install-recommends

# Install dasel
RUN curl -sSLf "$(curl -sSLf https://api.github.com/repos/tomwright/dasel/releases/latest | grep browser_download_url | grep linux_amd64 | grep -v .gz | cut -d\" -f 4)" -L -o /usr/bin/dasel && \
    chmod +x /usr/bin/dasel && \
    rm -rf /var/lib/apt/lists/* /root/.cache

# RUN add-apt-repository ppa:deadsnakes/ppa && apt update && apt install -y python3.11 python3.11-distutils && apt clean
# RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11


# Download and install Python 3.11
# RUN wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz && \
#     tar xzf Python-3.11.0.tgz && \
#     cd Python-3.11.0 && \
#     ./configure --enable-optimizations && \
#     make -j 4 && \
#     make altinstall && \
#     cd .. && \
#     rm -rf Python-3.11.0* 

# Install Poetry
# RUN curl -sSL https://install.python-poetry.org | python3.11 -

WORKDIR /code
RUN touch README.md

ENV PATH="${PATH}:/root/.local/bin"


# RUN python3.11 -m venv /code/venv

# Install dependencies without a virtual environment
RUN pip install --user fastapi langchain-core \
    langchain \
    pysqlite3-binary \
    chromadb \
    langchain-openai \
    firebase-admin \
    ffmpeg \
    pandoc \
    python-dotenv \
    langchain-chroma \
    uvicorn \
    langchainhub

COPY . /code/
COPY project /code/project

EXPOSE 8080

CMD HOME=/code

ENTRYPOINT ["python", "-m", "project.app"]

