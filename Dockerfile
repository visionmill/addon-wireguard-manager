ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache \
    bash \
    iproute2 \
    iptables \
    wireguard-tools \
    python3 \
    py3-pip \
    py3-flask \
    py3-qrcode \
    py3-pillow \
    py3-gunicorn

WORKDIR /app
COPY app/ /app/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
