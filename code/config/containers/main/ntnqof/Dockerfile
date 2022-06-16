FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /ntnqof
COPY --from=builder /go/src/5g-core-ntn/bin/ntnqof /usr/local/bin/ntnqof
ENTRYPOINT ["ntnqof"]
CMD ["-h"]