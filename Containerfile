FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install good-start and its dependencies
COPY . /opt/good-start
RUN cd /opt/good-start && uv pip install --system .

WORKDIR /workspace

ENTRYPOINT ["python", "-m", "good_start._entrypoint"]
