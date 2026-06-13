from __future__ import annotations
import re
from pathlib import Path

from PySide6.QtWidgets import QFileDialog

_FILTERS = "JSON (*.json);;Markdown (*.md);;Text (*.txt);;PDF (*.pdf)"
_EXT_MAP = {".json": "json", ".md": "md", ".txt": "txt", ".pdf": "pdf"}


def open_export_dialog(parent, title: str, default_name: str) -> tuple[str, str]:
    """Open a save dialog that updates the filename extension when the filter changes.
    Returns (filepath, fmt) or ('', '') if cancelled."""
    dialog = QFileDialog(parent, title)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setNameFilters(_FILTERS.split(";;"))
    dialog.selectFile(f"{default_name}.json")

    def _on_filter_changed(f: str) -> None:
        m = re.search(r'\*(\.\w+)', f)
        if m:
            current = dialog.selectedFiles()
            if current:
                dialog.selectFile(str(Path(current[0]).with_suffix(m.group(1))))

    dialog.filterSelected.connect(_on_filter_changed)

    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return "", ""

    files = dialog.selectedFiles()
    if not files or not files[0]:
        return "", ""

    filepath = files[0]
    m = re.search(r'\*(\.\w+)', dialog.selectedNameFilter())
    if m:
        filepath = str(Path(filepath).with_suffix(m.group(1)))

    return filepath, _EXT_MAP.get(Path(filepath).suffix.lower(), "json")
