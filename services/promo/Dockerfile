FROM golang:1.23-alpine AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY cmd ./cmd
COPY internal ./internal
RUN CGO_ENABLED=0 go build -o /promo ./cmd/server

FROM alpine:3.21
RUN apk add --no-cache wget
COPY --from=builder /promo /usr/local/bin/promo
EXPOSE 8081
CMD ["promo"]
