FROM alpine:3.10.1

RUN apk add --no-cache python3 && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools prometheus_client requests
COPY exporter.py /usr/local/bin
ENTRYPOINT ["python3", "-u", "/usr/local/bin/exporter.py"]
