from __future__ import annotations

import re
import socket
import ssl
import subprocess
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.tls_watchlist import (
    UNTRUSTED, WatchEntry, check_cert_expiry, load_watchlist, save_watchlist,
)


_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

def _parse_cert_date(s: str) -> datetime:
    """Parse SSL cert date without relying on locale (%b is locale-dependent)."""
    parts = s.split()
    if parts and parts[-1] in ("GMT", "UTC", "Z"):
        parts = parts[:-1]
    # parts: ['May', '5', '00:00:00', '2026']
    month  = _MONTHS.get(parts[0].lower(), 1)
    day    = int(parts[1])
    h, m, sec = (int(x) for x in parts[2].split(":"))
    year   = int(parts[3])
    return datetime(year, month, day, h, m, sec)


# ── Cert parsing from DER via openssl ─────────────────────────────────────────

def _parse_der(der: bytes) -> dict | None:
    """Convert DER cert to a getpeercert()-compatible dict via openssl."""
    try:
        pem = ssl.DER_cert_to_PEM_cert(der)
        proc = subprocess.run(
            ["openssl", "x509", "-noout", "-subject", "-issuer",
             "-dates", "-ext", "subjectAltName", "-serial"],
            input=pem, capture_output=True, text=True, timeout=5,
        )
        out = proc.stdout

        def _first(pattern: str) -> str:
            m = re.search(pattern, out, re.MULTILINE)
            return m.group(1).strip() if m else ""

        not_before_str = _first(r"^notBefore=(.+)")
        not_after_str  = _first(r"^notAfter=(.+)")
        if not not_before_str or not not_after_str:
            return None

        subject_line = _first(r"^subject=(.+)")
        cn_m = re.search(r"CN\s*=\s*([^,/\n]+)", subject_line)
        subject_cn = cn_m.group(1).strip() if cn_m else ""

        issuer_line  = _first(r"^issuer=(.+)")
        issuer_parts = re.findall(r"(?:O|CN)\s*=\s*([^,/\n]+)", issuer_line)
        issuer_str   = " — ".join(list(dict.fromkeys(p.strip() for p in issuer_parts))[:2])

        san_m = re.search(r"Subject Alternative Name:[^\n]*\n\s+(.+)", out)
        sans  = []
        if san_m:
            sans = [s.strip()[4:] for s in san_m.group(1).split(",")
                    if s.strip().startswith("DNS:")]

        serial = _first(r"^serial=([0-9A-Fa-f]+)")

        return {
            "notBefore":       not_before_str,
            "notAfter":        not_after_str,
            "subject":         ((("commonName", subject_cn),),) if subject_cn else (),
            "issuer":          (),
            "_issuer_str":     issuer_str,
            "subjectAltName":  tuple(("DNS", s) for s in sans),
            "serialNumber":    serial,
        }
    except Exception:
        return None


# ── Workers ───────────────────────────────────────────────────────────────────

class _TlsWorker(QThread):
    result = Signal(dict)
    error  = Signal(str)

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self._host = host
        self._port = port

    def run(self) -> None:
        try:
            self._run()
        except Exception as exc:
            self.error.emit(str(exc))

    def _run(self) -> None:
        host, port = self._host, self._port

        # Step 1 — connect unverified, get binary cert + connection info
        # (getpeercert() with CERT_NONE returns {}, must use binary_form=True)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE

        try:
            with socket.create_connection((host, port), timeout=10) as raw:
                with ctx.wrap_socket(raw, server_hostname=host) as s:
                    cert_der    = s.getpeercert(binary_form=True)
                    cipher_info = s.cipher()
                    protocol    = s.version()
        except socket.timeout:
            self.error.emit(tr("tls_err_timeout"))
            return
        except ConnectionRefusedError:
            self.error.emit(tr("tls_err_conn"))
            return
        except socket.gaierror:
            self.error.emit(tr("tls_err_resolve", host=host))
            return
        except OSError as exc:
            self.error.emit(str(exc))
            return
        except ssl.SSLError as exc:
            self.error.emit(tr("tls_err_ssl", msg=str(exc)))
            return

        # Step 2 — check validity
        valid        = True
        verify_error = None
        try:
            ctx_v = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=5) as raw:
                with ctx_v.wrap_socket(raw, server_hostname=host):
                    pass
        except ssl.SSLCertVerificationError as exc:
            valid        = False
            verify_error = str(exc)
        except Exception:
            pass

        # Step 3 — parse cert: try openssl, then re-connect verified as fallback
        cert = _parse_der(cert_der)
        if cert is None and valid:
            try:
                ctx_v = ssl.create_default_context()
                with socket.create_connection((host, port), timeout=5) as raw:
                    with ctx_v.wrap_socket(raw, server_hostname=host) as s:
                        cert = s.getpeercert()  # full dict only when verified
            except Exception:
                pass
        if cert is None:
            self.error.emit("Cannot parse certificate (openssl not available)")
            return

        # Step 4 — build result
        not_before = _parse_cert_date(cert["notBefore"])
        not_after  = _parse_cert_date(cert["notAfter"])
        days       = (not_after - datetime.utcnow()).days

        subject_cn = next(
            (v for rdn in cert.get("subject", ()) for k, v in rdn if k == "commonName"),
            host,
        )

        issuer = cert.get("_issuer_str") or " — ".join(
            list(dict.fromkeys(
                v for rdn in cert.get("issuer", ())
                for k, v in rdn if k in ("organizationName", "commonName")
            ))[:2]
        )

        sans = [v for kind, v in cert.get("subjectAltName", ()) if kind == "DNS"]

        self.result.emit({
            "subject_cn":   subject_cn,
            "sans":         sans,
            "issuer":       issuer,
            "not_before":   not_before,
            "not_after":    not_after,
            "days":         days,
            "serial":       cert.get("serialNumber", ""),
            "cipher_name":  cipher_info[0] if cipher_info else "",
            "cipher_bits":  cipher_info[2] if cipher_info else 0,
            "protocol":     protocol or "",
            "valid":        valid,
            "verify_error": verify_error,
        })


class _WatchlistWorker(QThread):
    entry_done = Signal(str, int, object)  # host, port, days_or_None
    all_done   = Signal()

    def __init__(self, entries: list[WatchEntry]) -> None:
        super().__init__()
        self._entries = entries

    def run(self) -> None:
        for e in self._entries:
            days = check_cert_expiry(e.host, e.port)
            self.entry_done.emit(e.host, e.port, days)
        self.all_done.emit()


class _ChainWorker(QThread):
    done = Signal(list)  # [(depth, cn, org), …] sorted depth 0 → N

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self._host = host
        self._port = port

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ["openssl", "s_client", "-connect", f"{self._host}:{self._port}",
                 "-servername", self._host],
                input=b"",
                capture_output=True,
                timeout=10,
            )
            chain = []
            for line in proc.stderr.decode("utf-8", errors="ignore").splitlines():
                if not line.startswith("depth="):
                    continue
                m = re.match(r"depth=(\d+)\s+(.*)", line)
                if not m:
                    continue
                depth = int(m.group(1))
                attrs = dict(re.findall(r"(\w+)\s*=\s*([^,\n]+?)(?=\s*,\s*\w+\s*=|$)", m.group(2)))
                chain.append((depth, attrs.get("CN", "").strip(), attrs.get("O", "").strip()))
            self.done.emit(sorted(chain, key=lambda x: x[0]))
        except FileNotFoundError:
            self.done.emit([])
        except Exception:
            self.done.emit([])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
    return lbl


def _row(label: str, value: str, value_color: str | None = None) -> QWidget:
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 2, 0, 2)
    lbl = QLabel(label + ":")
    lbl.setFixedWidth(110)
    lbl.setStyleSheet("color: gray; font-size: 12px;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    val = QLabel(value)
    val.setWordWrap(True)
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    style = "font-size: 12px;"
    if value_color:
        style += f" color: {value_color};"
    val.setStyleSheet(style)
    h.addWidget(lbl)
    h.addSpacing(8)
    h.addWidget(val, 1)
    return w


def _separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    return sep


# ── Main page ─────────────────────────────────────────────────────────────────

class TlsPage(QWidget):
    watchlist_status_changed = Signal(str)  # "ok" | "warning" | "expired"

    def __init__(self) -> None:
        super().__init__()
        self._worker: _TlsWorker | None = None
        self._chain_worker: _ChainWorker | None = None
        self._wl_worker: _WatchlistWorker | None = None
        self._wl_entries: list[WatchEntry] = load_watchlist()
        self._wl_results: dict[tuple[str, int], int | None] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(8)

        # ── Toolbar ───────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText(tr("tls_host_placeholder"))
        self._host_edit.returnPressed.connect(self._start)

        port_lbl = QLabel(tr("tls_port_label"))
        port_lbl.setStyleSheet("font-size: 12px;")
        self._port_edit = QLineEdit("443")
        self._port_edit.setFixedWidth(60)
        self._port_edit.returnPressed.connect(self._start)

        self._btn_check = QPushButton(tr("tls_btn_check"))
        self._btn_check.setFixedWidth(90)
        self._btn_check.clicked.connect(self._start)

        self._btn_stop = QPushButton(tr("tls_btn_stop"))
        self._btn_stop.setFixedWidth(70)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop)

        self._btn_watch = QPushButton("+ Watch")
        self._btn_watch.setFixedWidth(70)
        self._btn_watch.setToolTip("Add current host to TLS watchlist")
        self._btn_watch.clicked.connect(self._add_current_to_watchlist)

        bar.addWidget(self._host_edit, 1)
        bar.addWidget(port_lbl)
        bar.addWidget(self._port_edit)
        bar.addWidget(self._btn_check)
        bar.addWidget(self._btn_stop)
        bar.addWidget(self._btn_watch)
        root.addLayout(bar)

        # ── Scroll area for results ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._result_widget = QWidget()
        self._result_layout = QVBoxLayout(self._result_widget)
        self._result_layout.setContentsMargins(4, 4, 4, 4)
        self._result_layout.setSpacing(6)
        self._result_layout.addStretch(1)

        scroll.setWidget(self._result_widget)
        root.addWidget(scroll, 1)

        # ── Watchlist panel ───────────────────────────────────────────────
        root.addWidget(self._build_watchlist_panel())

    # ── Actions ───────────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        cli = get_cli_bar()
        if cli:
            h = self._host_edit.text().strip() or "<host>"
            p = self._port_edit.text().strip() or "443"
            cli.set_cmd(f"openssl s_client -connect {h}:{p} -servername {h} </dev/null | openssl x509 -noout -text")

    def _start(self) -> None:
        host = self._host_edit.text().strip()
        if not host:
            return

        try:
            port = int(self._port_edit.text().strip())
        except ValueError:
            port = 443

        self._clear_results()
        self._btn_check.setEnabled(False)
        self._btn_stop.setEnabled(True)

        # Update CLI bar
        cli = get_cli_bar()
        if cli:
            cli.set_cmd(f"openssl s_client -connect {host}:{port} -servername {host} </dev/null | openssl x509 -noout -text")

        # Status label while loading
        self._status_lbl = QLabel(tr("tls_checking"))
        self._status_lbl.setStyleSheet("font-size: 13px; color: gray;")
        self._result_layout.insertWidget(0, self._status_lbl)

        self._worker = _TlsWorker(host, port)
        self._worker.result.connect(lambda d: self._on_result(d, host, port))
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
        if self._chain_worker and self._chain_worker.isRunning():
            self._chain_worker.terminate()
        self._on_worker_done()

    def _on_worker_done(self) -> None:
        self._btn_check.setEnabled(True)
        self._btn_stop.setEnabled(False)

    def _clear_results(self) -> None:
        while self._result_layout.count() > 1:  # keep the trailing stretch
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Result rendering ──────────────────────────────────────────────────────

    def _on_error(self, msg: str) -> None:
        self._clear_results()
        lbl = QLabel(msg)
        lbl.setStyleSheet("font-size: 13px; color: #f38ba8;")
        lbl.setWordWrap(True)
        self._result_layout.insertWidget(0, lbl)

    def _on_result(self, data: dict, host: str, port: int) -> None:
        self._clear_results()

        days = data["days"]

        # Determine validity status + color
        if not data["valid"] or days < 0:
            status_text  = tr("tls_status_expired") if days < 0 else tr("tls_status_invalid")
            status_color = "#f38ba8"   # red
        elif days <= 30:
            status_text  = tr("tls_status_expiring")
            status_color = "#fab387"   # orange
        else:
            status_text  = tr("tls_status_valid")
            status_color = "#a6e3a1"   # green

        # ── Status header ─────────────────────────────────────────────────
        hdr = QLabel(f"  {data['subject_cn']}  —  {status_text}")
        hdr.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {status_color};"
            f" padding: 6px 10px; border-radius: 6px;"
        )
        idx = 0
        self._result_layout.insertWidget(idx, hdr); idx += 1

        # ── Certificate section ───────────────────────────────────────────
        self._result_layout.insertWidget(idx, _separator());         idx += 1
        self._result_layout.insertWidget(idx, _section_label(tr("tls_section_cert"))); idx += 1

        self._result_layout.insertWidget(idx, _row(tr("tls_lbl_subject"), data["subject_cn"])); idx += 1

        if data["sans"]:
            sans_str = ",  ".join(data["sans"][:8])
            if len(data["sans"]) > 8:
                sans_str += f"  (+{len(data['sans']) - 8})"
            self._result_layout.insertWidget(idx, _row(tr("tls_lbl_sans"), sans_str)); idx += 1

        self._result_layout.insertWidget(idx, _row(tr("tls_lbl_issuer"), data["issuer"])); idx += 1

        self._result_layout.insertWidget(
            idx, _row(tr("tls_lbl_valid_from"), data["not_before"].strftime("%Y-%m-%d"))
        ); idx += 1

        if days < 0:
            days_str  = tr("tls_expired_since", n=abs(days))
            days_col  = "#f38ba8"
        elif days <= 30:
            days_str  = tr("tls_days_remaining", n=days)
            days_col  = "#fab387"
        else:
            days_str  = tr("tls_days_remaining", n=days)
            days_col  = "#a6e3a1"

        expiry_text = data["not_after"].strftime("%Y-%m-%d") + "    " + days_str
        self._result_layout.insertWidget(
            idx, _row(tr("tls_lbl_valid_to"), expiry_text, days_col)
        ); idx += 1

        if data["serial"]:
            serial = ":".join(data["serial"][i:i+2] for i in range(0, min(len(data["serial"]), 20), 2))
            if len(data["serial"]) > 20:
                serial += "…"
            self._result_layout.insertWidget(idx, _row(tr("tls_lbl_serial"), serial)); idx += 1

        if data.get("verify_error"):
            self._result_layout.insertWidget(
                idx, _row(tr("tls_lbl_verify_err"), data["verify_error"], "#f38ba8")
            ); idx += 1

        # ── Connection section ────────────────────────────────────────────
        self._result_layout.insertWidget(idx, _separator());          idx += 1
        self._result_layout.insertWidget(idx, _section_label(tr("tls_section_conn"))); idx += 1
        self._result_layout.insertWidget(idx, _row(tr("tls_lbl_protocol"), data["protocol"])); idx += 1

        if data["cipher_name"]:
            cipher_str = data["cipher_name"]
            if data["cipher_bits"]:
                cipher_str += f"  ({data['cipher_bits']} bits)"
            self._result_layout.insertWidget(idx, _row(tr("tls_lbl_cipher"), cipher_str)); idx += 1

        # Placeholder for chain (filled async)
        self._result_layout.insertWidget(idx, _separator());  idx += 1
        self._chain_title = _section_label(tr("tls_section_chain"))
        self._result_layout.insertWidget(idx, self._chain_title); idx += 1
        self._chain_idx = idx

        # Launch chain worker
        self._chain_worker = _ChainWorker(host, port)
        self._chain_worker.done.connect(self._on_chain)
        self._chain_worker.start()

    def _on_chain(self, chain: list) -> None:
        if not chain:
            lbl = QLabel(tr("tls_chain_unavailable"))
            lbl.setStyleSheet("font-size: 12px; color: gray;")
            self._result_layout.insertWidget(self._chain_idx, lbl)
            return

        for depth, cn, org in chain:
            tag = ""
            if depth == 0:
                tag = f"  [{tr('tls_leaf')}]"
            elif depth == len(chain) - 1:
                tag = f"  [{tr('tls_root')}]"
            label = f"[{depth}]  {cn or org}{tag}"
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 12px; font-family: monospace;")
            self._result_layout.insertWidget(self._chain_idx + depth, lbl)

    # ── Watchlist ──────────────────────────────────────────────────────────────

    def _build_watchlist_panel(self) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setMaximumHeight(165)
        v = QVBoxLayout(frame)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(4)

        hdr = QHBoxLayout()
        title = QLabel("TLS Watchlist")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        hdr.addWidget(title)
        hdr.addStretch()

        self._wl_recheck_btn = QPushButton("↻ Re-check")
        self._wl_recheck_btn.setFixedWidth(85)
        self._wl_recheck_btn.clicked.connect(self.start_watchlist_check)
        hdr.addWidget(self._wl_recheck_btn)

        self._wl_remove_btn = QPushButton("− Remove")
        self._wl_remove_btn.setFixedWidth(75)
        self._wl_remove_btn.clicked.connect(self._remove_from_watchlist)
        hdr.addWidget(self._wl_remove_btn)

        v.addLayout(hdr)

        self._wl_list = QListWidget()
        self._wl_list.setFixedHeight(85)
        self._wl_list.setFrameShape(QFrame.Shape.NoFrame)
        self._wl_list.setStyleSheet("font-size: 12px; font-family: monospace;")
        v.addWidget(self._wl_list)

        add_bar = QHBoxLayout()
        add_bar.setSpacing(4)
        self._wl_host_edit = QLineEdit()
        self._wl_host_edit.setPlaceholderText("hostname or IP")
        self._wl_host_edit.returnPressed.connect(self._add_manual_to_watchlist)
        self._wl_port_spin = QSpinBox()
        self._wl_port_spin.setRange(1, 65535)
        self._wl_port_spin.setValue(443)
        self._wl_port_spin.setFixedWidth(65)
        add_btn = QPushButton("+ Add")
        add_btn.setFixedWidth(60)
        add_btn.clicked.connect(self._add_manual_to_watchlist)
        add_bar.addWidget(self._wl_host_edit, 1)
        add_bar.addWidget(self._wl_port_spin)
        add_bar.addWidget(add_btn)
        v.addLayout(add_bar)

        self._refresh_wl_list()
        return frame

    def _refresh_wl_list(self) -> None:
        self._wl_list.clear()
        for e in self._wl_entries:
            days = self._wl_results.get((e.host, e.port))
            item = QListWidgetItem(self._wl_entry_text(e.host, e.port, days))
            item.setForeground(QColor(self._wl_entry_color(days)))
            self._wl_list.addItem(item)

    _PENDING = object()  # sentinel: entry queued but not yet checked

    @staticmethod
    def _wl_entry_text(host: str, port: int, days) -> str:
        base = f"{host}:{port}"
        if days is TlsPage._PENDING:
            return f"{base:<32}  … (checking)"
        if days is None:
            return f"{base:<32}  — (unreachable)"
        if days == UNTRUSTED:
            return f"{base:<32}  ⚠ Invalid / untrusted cert"
        if days < 0:
            return f"{base:<32}  EXPIRED {abs(days)} days ago"
        if days <= 30:
            return f"{base:<32}  ⚠ {days} days remaining"
        return f"{base:<32}  ✓ {days} days remaining"

    @staticmethod
    def _wl_entry_color(days) -> str:
        if days is TlsPage._PENDING:
            return "gray"
        if days is None:
            return "#6c7086"   # dimmer gray — unreachable
        if days == UNTRUSTED:
            return "#fab387"   # orange — invalid but not expired
        if days < 0:
            return "#f38ba8"   # red — expired
        if days <= 30:
            return "#fab387"   # orange — expiring soon
        return "#a6e3a1"       # green — ok

    def _add_current_to_watchlist(self) -> None:
        host = self._host_edit.text().strip()
        if not host:
            return
        try:
            port = int(self._port_edit.text().strip())
        except ValueError:
            port = 443
        self._add_entry(WatchEntry(host, port))

    def _add_manual_to_watchlist(self) -> None:
        host = self._wl_host_edit.text().strip()
        if not host:
            return
        self._add_entry(WatchEntry(host, self._wl_port_spin.value()))
        self._wl_host_edit.clear()

    def _add_entry(self, entry: WatchEntry) -> None:
        if any(e.host == entry.host and e.port == entry.port for e in self._wl_entries):
            return
        self._wl_entries.append(entry)
        save_watchlist(self._wl_entries)
        self._refresh_wl_list()

    def _remove_from_watchlist(self) -> None:
        row = self._wl_list.currentRow()
        if 0 <= row < len(self._wl_entries):
            e = self._wl_entries.pop(row)
            self._wl_results.pop((e.host, e.port), None)
            save_watchlist(self._wl_entries)
            self._refresh_wl_list()
            self._emit_worst_status()

    def start_watchlist_check(self) -> None:
        if not self._wl_entries:
            return
        if self._wl_worker and self._wl_worker.isRunning():
            return
        # Mark all entries as pending before starting
        for e in self._wl_entries:
            self._wl_results[(e.host, e.port)] = TlsPage._PENDING
        self._refresh_wl_list()
        self._wl_recheck_btn.setEnabled(False)
        self._wl_worker = _WatchlistWorker(list(self._wl_entries))
        self._wl_worker.entry_done.connect(self._on_wl_entry_done)
        self._wl_worker.all_done.connect(self._on_wl_all_done)
        self._wl_worker.start()

    def _on_wl_entry_done(self, host: str, port: int, days) -> None:
        self._wl_results[(host, port)] = days
        self._refresh_wl_list()

    def _on_wl_all_done(self) -> None:
        self._wl_recheck_btn.setEnabled(True)
        self._emit_worst_status()

    def _emit_worst_status(self) -> None:
        values = list(self._wl_results.values())
        if not values:
            return
        if any(d is not None and d != UNTRUSTED and d < 0 for d in values):
            self.watchlist_status_changed.emit("expired")
        elif any(d is not None and (d == UNTRUSTED or 0 <= d < 30) for d in values):
            self.watchlist_status_changed.emit("warning")
        else:
            self.watchlist_status_changed.emit("ok")
