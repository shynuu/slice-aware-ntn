FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /qof
COPY --from=builder /go/src/5g-core-ntn/free5gc/bin/qof /usr/local/bin/qof
COPY ./entrypoint.sh /qof/entrypoint.sh
ENTRYPOINT [ "./entrypoint.sh" ]