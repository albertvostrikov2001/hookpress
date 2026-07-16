"""Prometheus metrics registry."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

HTTP_REQUESTS = Counter(
    "hookpress_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_ERRORS = Counter(
    "hookpress_http_errors_total",
    "Total HTTP error responses",
    ["method", "path", "status"],
)

AUTH_LOGINS = Counter(
    "hookpress_auth_logins_total",
    "Successful dev-login and refresh operations",
    ["type"],
)

BILLING_WEBHOOKS = Counter(
    "hookpress_billing_webhooks_total",
    "Payment webhook deliveries",
    ["result"],
)

CELERY_QUEUE_DEPTH = Gauge(
    "hookpress_celery_queue_depth",
    "Approximate Celery queue depth (stub until broker introspection)",
    ["queue"],
)

WS_CONNECTIONS = Gauge(
    "hookpress_ws_connections",
    "Active WebSocket connections",
)

STORAGE_BYTES = Counter(
    "hookpress_storage_bytes_total",
    "Bytes stored or retrieved from object storage",
    ["bucket", "operation"],
)

# Stub queue depths for dashboard wiring until Celery introspection lands.
CELERY_QUEUE_DEPTH.labels(queue="default").set(0)
CELERY_QUEUE_DEPTH.labels(queue="media").set(0)
CELERY_QUEUE_DEPTH.labels(queue="charts").set(0)


def record_storage_bytes(bucket: str, operation: str, nbytes: int) -> None:
    if nbytes > 0:
        STORAGE_BYTES.labels(bucket=bucket, operation=operation).inc(nbytes)


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
