FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim AS free5gc-amf
WORKDIR /amf
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    iproute2 tcpdump iputils-ping \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /go/src/5g-core-ntn/free5gc/bin/amf /usr/local/bin/amf