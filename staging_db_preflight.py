"""Fail-closed safety checks for disposable RKU ONE staging databases.

This module does not connect or mutate a database. Use before any staging
schema setup or test write; never treat this as permission to deploy.
"""
import ipaddress
from urllib.parse import urlsplit, unquote


def assert_disposable_staging_url(url: str) -> None:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Staging database URL is required")
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        dbname = unquote(parsed.path.removeprefix("/"))
        port = parsed.port
    except (ValueError, AttributeError) as exc:
        raise ValueError("Invalid staging database URL") from exc
    if parsed.scheme not in ("postgresql", "postgres") or not host or not dbname:
        raise ValueError("Valid PostgreSQL staging URL required")
    if parsed.query or parsed.fragment or parsed.username is None or parsed.password is None:
        raise ValueError("Use a dedicated staging URL without query overrides")
    if not dbname.endswith("_vip_test"):
        raise ValueError("Refusing database without _vip_test suffix")
    if host.lower() not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Only local disposable PostgreSQL hosts are allowed")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid PostgreSQL port")
    if parsed.hostname != "localhost":
        try:
            if not ipaddress.ip_address(parsed.hostname).is_loopback:
                raise ValueError("Staging database must be loopback-only")
        except ValueError as exc:
            raise ValueError("Invalid loopback staging host") from exc
