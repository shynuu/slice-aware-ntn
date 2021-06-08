FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /udr
COPY --from=builder /go/src/free5gc/bin/udr /usr/local/bin/udr
ENTRYPOINT ["udr"]
CMD ["-h"]