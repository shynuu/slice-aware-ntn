FROM debian:buster-slim

RUN apt-get update && apt-get install -y build-essential git iproute2 tcpdump iptables
WORKDIR /iperf
RUN git clone https://git.code.sf.net/p/iperf2/code iperf2-source
WORKDIR /iperf/iperf2-source
RUN ./configure
RUN make
RUN make install

WORKDIR /application
RUN mkdir /application/results-sa
RUN mkdir /application/results-non-sa