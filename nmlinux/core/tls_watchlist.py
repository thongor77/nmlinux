from __future__ import annotations

import json
import re
import socket
import ssl
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

CONFIG_DIR    = Path.home() / ".config" / "nmlinux"
WATCHLIST_FILE = CONFIG_DIR / "tls_watchlist.json"

UNTRUSTED = -10000  # cert reachable + not expired, but chain verification failed

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_date(s: str) -> datetime:
    parts = s.split()
    if parts and parts[-1] in ("GMT", "UTC", "Z"):
        parts = parts[:-1]
    month = _MONTHS.get(parts[0].lower(), 1)
    day   = int(parts[1])
    h, m, sec = (int(x) for x in parts[2].split(":"))
    year  = int(parts[3])
    return datetime(year, month, day, h, m, sec)


@dataclass
class WatchEntry:
    host: str
    port: int = 443


def load_watchlist() -> list[WatchEntry]:
    try:
        data = json.loads(WATCHLIST_FILE.read_text())
        return [WatchEntry(e["host"], int(e.get("port", 443))) for e in data]
    except Exception:
        return []


def save_watchlist(entries: list[WatchEntry]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    WATCHLIST_FILE.write_text(json.dumps([asdict(e) for e in entries], indent=2))


def check_cert_expiry(host: str, port: int, timeout: int = 5) -> int | None:
    """Return days until cert expiry (negative = expired, UNTRUSTED = invalid chain).
    None means the host is unreachable — not counted as an alert."""
    # Step 1: get DER cert without verifying chain
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as s:
                cert_der = s.getpeercert(binary_form=True)
    except Exception:
        return None

    # Step 2: parse expiry date
    days: int | None = None
    try:
        pem  = ssl.DER_cert_to_PEM_cert(cert_der)
        proc = subprocess.run(
            ["openssl", "x509", "-noout", "-enddate"],
            input=pem, capture_output=True, text=True, timeout=3,
        )
        m = re.search(r"notAfter=(.+)", proc.stdout)
        if m:
            days = (_parse_date(m.group(1).strip()) - datetime.utcnow()).days
    except Exception:
        pass

    # Step 3: check chain trust
    trusted = True
    try:
        ctx_v = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx_v.wrap_socket(raw, server_hostname=host):
                pass
    except ssl.SSLError:
        # Catches SSLCertVerificationError and any other SSL handshake failure
        trusted = False
    except Exception:
        pass  # network hiccup — don't change trusted status

    if days is None:
        # openssl not available — fall back to verified connection for days
        if trusted:
            try:
                ctx_v = ssl.create_default_context()
                with socket.create_connection((host, port), timeout=timeout) as raw:
                    with ctx_v.wrap_socket(raw, server_hostname=host) as s:
                        cert = s.getpeercert()
                days = (_parse_date(cert["notAfter"]) - datetime.utcnow()).days
            except Exception:
                return None
        else:
            return UNTRUSTED

    if days is not None and days >= 0 and not trusted:
        return UNTRUSTED  # not expired, but chain fails (self-signed, wrong CA…)

    return days
