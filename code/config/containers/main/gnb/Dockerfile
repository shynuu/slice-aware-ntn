FROM golang:1.14 AS go-builder

WORKDIR /gtp-dscp
RUN git clone https://github.com/shynuu/gtp-dscp.git /gtp-dscp
RUN go build -o gtp-dscp main.go

FROM shynuu/sa-ntn:ueransim as builder
FROM debian:buster-slim
WORKDIR /ueransim
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    lksctp-tools iproute2 tcpdump iputils-ping iptables \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /compile/UERANSIM/build/nr-gnb /usr/local/bin/nr-gnb
COPY --from=go-builder /gtp-dscp/gtp-dscp /usr/local/sbin/gtp-dscp