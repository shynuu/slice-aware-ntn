FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /udm
COPY --from=builder /go/src/5g-core-ntn/free5gc/bin/udm /usr/local/bin/udm
ENTRYPOINT ["udm"]
CMD ["-h"]