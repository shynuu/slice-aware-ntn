FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /udr
COPY --from=builder /go/src/5g-core-ntn/free5gc/bin/udr /usr/local/bin/udr
ENTRYPOINT ["udr"]
CMD ["-h"]