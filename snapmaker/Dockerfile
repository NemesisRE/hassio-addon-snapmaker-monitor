FROM ghcr.io/hassio-addons/base:18.0.3

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy Python requirements file
COPY requirements.txt /tmp/

# Copy source files
COPY src/smStatus.py /app/smStatus.py

RUN apk add --no-cache py3-pip python3
RUN pip install -r /tmp/requirements.txt
RUN apk del --no-cache --purge

RUN /usr/bin/python /app/smStatus.py
