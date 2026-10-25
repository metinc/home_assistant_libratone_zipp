"""Adapt the upstream client's IP-based UDP routing to configured hostnames."""
from __future__ import annotations

import socket

# Prefer vendored lib during dev. Fall back to PyPI if not present.
try:
    from .vendor.python_libratone_zipp.python_libratone_zipp import (
        LibratoneZipp as BaseLibratoneZipp,
    )
except ImportError:  # pragma: no cover
    from python_libratone_zipp import LibratoneZipp as BaseLibratoneZipp


class LibratoneZipp(BaseLibratoneZipp):
    """Resolve the IPv4 transport address without changing the HA identity."""

    def __init__(self, host: str):
        self.configured_host = host
        # The upstream hub registers clients by host, but dispatches replies by
        # source IPv4 address. Resolve before registration, not only when sending.
        super().__init__(socket.gethostbyname(host))
