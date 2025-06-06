FROM debian:bookworm

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data
#COPY requirements.txt .
RUN git clone https://github.com/koffienl/M3Usort

WORKDIR /data/M3Usort

# Create venv and install dependencies inside it
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# COPY ./M3Usort/ /data/M3Usort

CMD ["/venv/bin/python", "/data/M3Usort/run.py"]
