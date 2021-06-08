FROM shynuu/sa-ntn:ueransim as builder
FROM debian:buster-slim

RUN apt-get update && apt-get install -y build-essential git

WORKDIR /iperf
RUN git clone https://git.code.sf.net/p/iperf2/code iperf2-source
WORKDIR /iperf/iperf2-source
RUN ./configure
RUN make
RUN make install

WORKDIR /ue
RUN touch app.sh
RUN mkdir /ue/results
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    lksctp-tools iproute2 tcpdump iputils-ping \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /compile/UERANSIM/build/nr-ue /usr/local/bin/nr-ue
ENTRYPOINT ["nr-ue"]
CMD ["--help"]