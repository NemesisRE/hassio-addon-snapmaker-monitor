ARG BUILD_FROM=ghcr.io/hassio-addons/base:18.0.3
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy Python requirements file
COPY requirements.txt /tmp/

COPY ../smStatus.py /app/smStatus.py

# Setup base
# hadolint ignore=DL3003,DL3042
RUN \
  apk add --no-cache --virtual .build-dependencies \
  build-base=0.5-r3 \
  py3-pip=25.1.1-r0 \
  python3=3.12.11-r0 \
  \
  && pip install -r /tmp/requirements.txt \
  \
  && apk del --no-cache --purge .build-dependencies

  RUN python /app/smStatus.py
