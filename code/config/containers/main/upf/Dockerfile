FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim

RUN apt-get update && apt-get install -y build-essential git
WORKDIR /iperf
RUN git clone https://git.code.sf.net/p/iperf2/code iperf2-source
WORKDIR /iperf/iperf2-source
RUN ./configure
RUN make
RUN make install

WORKDIR /upf
RUN touch app.sh
RUN mkdir /upf/results
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    libmnl0 libyaml-0-2 iproute2 iptables tcpdump iputils-ping \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /go/src/free5gc/NFs/upf/build/bin/free5gc-upfd /usr/local/bin/free5gc-upfd 
COPY --from=builder /go/src/free5gc/NFs/upf/build/updk/src/third_party/libgtp5gnl/lib/libgtp5gnl.so.0 /usr/local/lib/libgtp5gnl.so.0
COPY --from=builder /go/src/free5gc/NFs/upf/build/utlt_logger/liblogger.so /usr/local/lib/liblogger.so
RUN ldconfig