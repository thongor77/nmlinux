from __future__ import annotations
import json
import subprocess
import platform
from datetime import datetime
from pathlib import Path


def _collect_interfaces() -> list[dict]:
    try:
        r = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True, timeout=5)
        return json.loads(r.stdout) if r.returncode == 0 else []
    except Exception:
        return []


def _collect_routes() -> list[dict]:
    try:
        r = subprocess.run(["ip", "-j", "route"], capture_output=True, text=True, timeout=5)
        return json.loads(r.stdout) if r.returncode == 0 else []
    except Exception:
        return []


def _collect_dns(resolv_path: str = "/etc/resolv.conf") -> list[str]:
    try:
        lines = Path(resolv_path).read_text().splitlines()
        return [line.split()[1] for line in lines if line.startswith("nameserver")]
    except Exception:
        return []


def collect_snapshot() -> dict:
    """Return a dict snapshot of the current network state."""
    return {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "interfaces": _collect_interfaces(),
        "routes": _collect_routes(),
        "dns": _collect_dns(),
    }


def _dict_to_text_lines(data: dict, indent: int = 0) -> list[str]:
    lines = []
    pad = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.extend(_dict_to_text_lines(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{pad}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.extend(_dict_to_text_lines(item, indent + 1))
                    lines.append(f"{pad}  ---")
                else:
                    lines.append(f"{pad}  - {item}")
        else:
            lines.append(f"{pad}{key}: {value}")
    return lines


def to_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_text(data: dict) -> str:
    ts = data.get("timestamp", datetime.now().isoformat())
    header = [f"nmlinux Export — {ts}", "=" * 60, ""]
    return "\n".join(header + _dict_to_text_lines(data))


def _dict_to_markdown_lines(data: dict, level: int = 2) -> list[str]:
    lines: list[str] = []
    heading = "#" * level
    for key, value in data.items():
        if key == "timestamp":
            continue
        title = key.replace("_", " ").title()
        if isinstance(value, list) and value and isinstance(value[0], dict):
            lines.append(f"\n{heading} {title}\n")
            headers = list(value[0].keys())
            lines.append("| " + " | ".join(h.replace("_", " ") for h in headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
            for item in value:
                row = " | ".join(str(item.get(h, "")) for h in headers)
                lines.append(f"| {row} |")
        elif isinstance(value, list):
            lines.append(f"\n{heading} {title}\n")
            for item in value:
                lines.append(f"- `{item}`")
        elif isinstance(value, dict):
            lines.append(f"\n{heading} {title}\n")
            lines.extend(_dict_to_markdown_lines(value, level + 1))
        else:
            lines.append(f"**{title}:** {value}  ")
    return lines


def to_markdown(data: dict) -> str:
    ts = data.get("timestamp", datetime.now().isoformat())
    header = ["# nmlinux Export", "", f"**Date:** {ts}  ", ""]
    return "\n".join(header + _dict_to_markdown_lines(data))


def to_pdf(data: dict, filepath: str) -> str | None:
    """Generate a PDF report. Returns error message string if reportlab is missing."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as rl_canvas
    except (ImportError, TypeError):
        return "PDF export requires 'reportlab'. Install with: pip install reportlab"

    c = rl_canvas.Canvas(filepath, pagesize=A4)
    y = 800

    def maybe_new_page() -> None:
        nonlocal y
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 800

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "nmlinux Network Report")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Date: {data.get('timestamp', '')}")
    y -= 10

    for key, value in data.items():
        if key == "timestamp":
            continue
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, key.replace("_", " ").title())
        y -= 16
        c.setFont("Helvetica", 10)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        c.drawString(70, y, f"{k}: {v}")
                        y -= 14
                        maybe_new_page()
                    y -= 4
                else:
                    c.drawString(70, y, f"- {item}")
                    y -= 14
                    maybe_new_page()
        elif not isinstance(value, dict):
            c.drawString(70, y, str(value))
            y -= 14
            maybe_new_page()

    c.save()
    return None


def save_export(data: dict, fmt: str, filepath: str) -> str | None:
    """Serialize data to filepath in the given format.
    fmt: 'json' | 'txt' | 'md' | 'pdf'
    Returns an error message string on failure, None on success."""
    try:
        if fmt == "json":
            Path(filepath).write_text(to_json(data), encoding="utf-8")
        elif fmt == "txt":
            Path(filepath).write_text(to_text(data), encoding="utf-8")
        elif fmt == "md":
            Path(filepath).write_text(to_markdown(data), encoding="utf-8")
        elif fmt == "pdf":
            return to_pdf(data, filepath)
        else:
            return f"Unsupported format: {fmt!r}"
    except OSError as e:
        return str(e)
    return None
