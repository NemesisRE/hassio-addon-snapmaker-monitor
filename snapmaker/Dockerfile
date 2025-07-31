FROM ghcr.io/hassio-addons/base:18.0.3

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /app

# Copy Python requirements file
COPY requirements.txt ./

# Copy source files
COPY src/smStatus.py ./smStatus.py

RUN apk add --no-cache py3-pip python3
RUN pip install -r requirements.txt
RUN apk del --no-cache --purge

ENTRYPOINT [ "/usr/bin/python", "/app/smStatus.py" ]
