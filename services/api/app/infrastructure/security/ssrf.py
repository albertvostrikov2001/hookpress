"""SSRF guards for outbound HTTP fetches."""

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.errors import AppError

_BLOCKED_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    for network in _BLOCKED_NETWORKS:
        if ip in network:
            return True
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast


def validate_public_url(url: str) -> str:
    """Validate URL scheme/host and ensure resolved IPs are not private."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise AppError("invalid_url", "Only http/https URLs are allowed", status_code=400)
    host = parsed.hostname
    if not host:
        raise AppError("invalid_url", "URL must include a hostname", status_code=400)
    if host.lower() in {"localhost", "metadata.google.internal"}:
        raise AppError("ssrf_blocked", "Private or local URLs are not allowed", status_code=403)

    try:
        addr_infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise AppError("invalid_url", f"Could not resolve host: {host}", status_code=400) from exc

    for info in addr_infos:
        ip_str = info[4][0]
        ip = ipaddress.ip_address(ip_str)
        if _is_blocked_ip(ip):
            raise AppError("ssrf_blocked", "Private or local URLs are not allowed", status_code=403)

    return url
