# Ping Monitor Saved Targets Directory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manually-curated, persistent directory of saved ping targets to `PingPage`, so hosts being monitored can be re-started after the app closes without retyping them, plus a one-click way to save a host that's already being monitored.

**Architecture:** A new `PingTarget` dataclass + `_PingTargetStore` (flat JSON list at `~/.local/share/nmlinux/ping_targets.json`), following the exact pattern already used by `WolHost`/`_WolStore` in `nmlinux/pages/wol.py`. `PingPage` is restructured from a single-column layout into a `QSplitter` with a new left directory panel (list + add/edit/delete/start, small form) and the existing toolbar+table moved into a right panel unchanged. A new ★ button on each live-monitoring table row saves that host into the directory.

**Tech Stack:** Python, PySide6 (Qt widgets), dataclasses, JSON file storage, pytest.

## Global Constraints

- No new external dependencies.
- Directory is a flat list — no groups/folders (per spec: "SSH but simpler").
- No auto-resume of monitoring on app launch — starting a saved target is always a manual action (per spec, this was an explicit user choice over auto-resume).
- Storage path: `~/.local/share/nmlinux/ping_targets.json`, same directory convention as `wol_hosts.json` / `ssh_connections.json`.
- All new user-facing strings go through `tr()` and must be added in all 8 languages (fr/en/es/de/it/pt/ja/zh), matching the existing `i18n.py` block order.
- Corrupt/missing store file → empty list, no dialog, no crash (matches `_WolStore`/`SshStore` behavior).

---

### Task 1: `PingTarget` dataclass and `_PingTargetStore`

**Files:**
- Modify: `nmlinux/pages/ping.py` (add new classes near the top, after imports, before `PingWorker`)
- Create: `tests/test_ping_targets.py`

**Interfaces:**
- Produces: `PingTarget(name: str = '', host: str = '', interval: int = 2)` — a dataclass (auto `__eq__`).
- Produces: `_PingTargetStore(path: Path | None = None)` with methods `all() -> list[PingTarget]`, `add(target: PingTarget) -> None`, `update(idx: int, target: PingTarget) -> None`, `remove(idx: int) -> None`, `has_host(host: str) -> bool`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ping_targets.py`:

```python
from __future__ import annotations

from nmlinux.pages.ping import PingTarget, _PingTargetStore


def test_store_starts_empty_when_file_missing(tmp_path):
    store = _PingTargetStore(tmp_path / 'missing.json')
    assert store.all() == []


def test_add_persists_and_reloads(tmp_path):
    path = tmp_path / 'targets.json'
    store = _PingTargetStore(path)
    store.add(PingTarget(name='Spain DNS', host='8.8.8.8', interval=5))

    reloaded = _PingTargetStore(path)
    assert reloaded.all() == [PingTarget(name='Spain DNS', host='8.8.8.8', interval=5)]


def test_update_replaces_entry_at_index(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    store.add(PingTarget(name='A', host='1.1.1.1'))
    store.update(0, PingTarget(name='B', host='2.2.2.2'))
    assert store.all() == [PingTarget(name='B', host='2.2.2.2')]


def test_remove_deletes_entry_at_index(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    store.add(PingTarget(name='A', host='1.1.1.1'))
    store.add(PingTarget(name='B', host='2.2.2.2'))
    store.remove(0)
    assert store.all() == [PingTarget(name='B', host='2.2.2.2')]


def test_load_corrupt_json_returns_empty_list(tmp_path):
    path = tmp_path / 'targets.json'
    path.write_text('not valid json {')
    store = _PingTargetStore(path)
    assert store.all() == []


def test_has_host_true_when_present(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    store.add(PingTarget(name='A', host='1.1.1.1'))
    assert store.has_host('1.1.1.1') is True


def test_has_host_false_when_absent(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    assert store.has_host('1.1.1.1') is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/claude-projects/nmlinux && python3 -m pytest tests/test_ping_targets.py -v`

Expected: collection error / `ImportError: cannot import name 'PingTarget' from 'nmlinux.pages.ping'` — the classes don't exist yet.

- [ ] **Step 3: Add the imports needed**

In `nmlinux/pages/ping.py`, replace:

```python
from __future__ import annotations

import re
import subprocess
import time as _time
from dataclasses import dataclass, field
```

with:

```python
from __future__ import annotations

import json
import re
import subprocess
import time as _time
from dataclasses import asdict, dataclass, field
from pathlib import Path
```

- [ ] **Step 4: Implement `PingTarget` and `_PingTargetStore`**

In `nmlinux/pages/ping.py`, immediately after the import block (before `class PingWorker(QThread):`), add:

```python
_TARGET_STORE_PATH = Path.home() / '.local' / 'share' / 'nmlinux' / 'ping_targets.json'


# ── Saved targets directory (data model) ──────────────────────────────────

@dataclass
class PingTarget:
    name:     str = ''
    host:     str = ''
    interval: int = 2


class _PingTargetStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _TARGET_STORE_PATH
        self._targets: list[PingTarget] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                fields = PingTarget.__dataclass_fields__
                self._targets = [
                    PingTarget(**{k: v for k, v in d.items() if k in fields})
                    for d in raw
                ]
            except Exception:
                self._targets = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([asdict(t) for t in self._targets], indent=2, ensure_ascii=False)
        )

    def all(self) -> list[PingTarget]:
        return list(self._targets)

    def add(self, target: PingTarget) -> None:
        self._targets.append(target)
        self._save()

    def update(self, idx: int, target: PingTarget) -> None:
        self._targets[idx] = target
        self._save()

    def remove(self, idx: int) -> None:
        del self._targets[idx]
        self._save()

    def has_host(self, host: str) -> bool:
        return any(t.host == host for t in self._targets)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/claude-projects/nmlinux && python3 -m pytest tests/test_ping_targets.py -v`

Expected: `7 passed`

- [ ] **Step 6: Run the full test suite to check for regressions**

Run: `cd ~/claude-projects/nmlinux && python3 -m pytest tests/ -q`

Expected: all tests pass (138 total: 132 existing + this task's 6 new — note 6, not 7, since one test file may report differently; confirm exact count matches `132 + <new count added>` with no failures)

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/nmlinux
git add nmlinux/pages/ping.py tests/test_ping_targets.py
git commit -m "Add PingTarget dataclass and _PingTargetStore for saved ping targets"
```

---

### Task 2: i18n keys for the directory panel

**Files:**
- Modify: `nmlinux/core/i18n.py`

**Interfaces:**
- Produces: 16 new translation keys, present in all 8 language blocks: `ping_dir_title`, `ping_dir_add_btn`, `ping_dir_edit_btn`, `ping_dir_delete_btn`, `ping_dir_start_btn`, `ping_dir_save_btn`, `ping_dir_cancel_btn`, `ping_dir_save_tooltip`, `ping_dir_lbl_name`, `ping_dir_lbl_host`, `ping_dir_lbl_interval`, `ping_dir_ph_name`, `ping_dir_form_title_new`, `ping_dir_form_title_edit`, `ping_dir_dlg_del_title`, `ping_dir_dlg_del_msg`.

- [ ] **Step 1: Confirm insertion anchor is unique per language block**

Run: `cd ~/claude-projects/nmlinux && grep -n '"ping_timeout":' nmlinux/core/i18n.py`

Expected: exactly 8 lines (one per language block, in fr/en/es/de/it/pt/ja/zh order — this is the existing order established elsewhere in the file and confirmed by the earlier `inv_refresh_empty_btn` insertion in this same session).

- [ ] **Step 2: Run the insertion script**

```bash
cd ~/claude-projects/nmlinux && python3 - << 'EOF'
path = "nmlinux/core/i18n.py"
with open(path, encoding="utf-8") as f:
    content = f.read()

new_keys = {
    "fr": {
        "ping_dir_title": "Cibles enregistrées",
        "ping_dir_add_btn": "Ajouter",
        "ping_dir_edit_btn": "Modifier",
        "ping_dir_delete_btn": "Supprimer",
        "ping_dir_start_btn": "▶  Surveiller",
        "ping_dir_save_btn": "Enregistrer",
        "ping_dir_cancel_btn": "Annuler",
        "ping_dir_save_tooltip": "Enregistrer dans l'annuaire",
        "ping_dir_lbl_name": "Nom :",
        "ping_dir_lbl_host": "Hôte :",
        "ping_dir_lbl_interval": "Intervalle :",
        "ping_dir_ph_name": "Serveur Espagne",
        "ping_dir_form_title_new": "Nouvelle cible",
        "ping_dir_form_title_edit": "Modifier la cible",
        "ping_dir_dlg_del_title": "Supprimer",
        "ping_dir_dlg_del_msg": "Supprimer « {name} » ?",
    },
    "en": {
        "ping_dir_title": "Saved targets",
        "ping_dir_add_btn": "Add",
        "ping_dir_edit_btn": "Edit",
        "ping_dir_delete_btn": "Delete",
        "ping_dir_start_btn": "▶  Monitor",
        "ping_dir_save_btn": "Save",
        "ping_dir_cancel_btn": "Cancel",
        "ping_dir_save_tooltip": "Save to directory",
        "ping_dir_lbl_name": "Name:",
        "ping_dir_lbl_host": "Host:",
        "ping_dir_lbl_interval": "Interval:",
        "ping_dir_ph_name": "Spain server",
        "ping_dir_form_title_new": "New target",
        "ping_dir_form_title_edit": "Edit target",
        "ping_dir_dlg_del_title": "Delete",
        "ping_dir_dlg_del_msg": "Delete «{name}»?",
    },
    "es": {
        "ping_dir_title": "Objetivos guardados",
        "ping_dir_add_btn": "Agregar",
        "ping_dir_edit_btn": "Editar",
        "ping_dir_delete_btn": "Eliminar",
        "ping_dir_start_btn": "▶  Supervisar",
        "ping_dir_save_btn": "Guardar",
        "ping_dir_cancel_btn": "Cancelar",
        "ping_dir_save_tooltip": "Guardar en el directorio",
        "ping_dir_lbl_name": "Nombre:",
        "ping_dir_lbl_host": "Host:",
        "ping_dir_lbl_interval": "Intervalo:",
        "ping_dir_ph_name": "Servidor España",
        "ping_dir_form_title_new": "Nuevo objetivo",
        "ping_dir_form_title_edit": "Editar objetivo",
        "ping_dir_dlg_del_title": "Eliminar",
        "ping_dir_dlg_del_msg": "¿Eliminar «{name}»?",
    },
    "de": {
        "ping_dir_title": "Gespeicherte Ziele",
        "ping_dir_add_btn": "Hinzufügen",
        "ping_dir_edit_btn": "Bearbeiten",
        "ping_dir_delete_btn": "Löschen",
        "ping_dir_start_btn": "▶  Überwachen",
        "ping_dir_save_btn": "Speichern",
        "ping_dir_cancel_btn": "Abbrechen",
        "ping_dir_save_tooltip": "Im Verzeichnis speichern",
        "ping_dir_lbl_name": "Name:",
        "ping_dir_lbl_host": "Host:",
        "ping_dir_lbl_interval": "Intervall:",
        "ping_dir_ph_name": "Server Spanien",
        "ping_dir_form_title_new": "Neues Ziel",
        "ping_dir_form_title_edit": "Ziel bearbeiten",
        "ping_dir_dlg_del_title": "Löschen",
        "ping_dir_dlg_del_msg": "«{name}» löschen?",
    },
    "it": {
        "ping_dir_title": "Obiettivi salvati",
        "ping_dir_add_btn": "Aggiungi",
        "ping_dir_edit_btn": "Modifica",
        "ping_dir_delete_btn": "Elimina",
        "ping_dir_start_btn": "▶  Monitora",
        "ping_dir_save_btn": "Salva",
        "ping_dir_cancel_btn": "Annulla",
        "ping_dir_save_tooltip": "Salva nell'elenco",
        "ping_dir_lbl_name": "Nome:",
        "ping_dir_lbl_host": "Host:",
        "ping_dir_lbl_interval": "Intervallo:",
        "ping_dir_ph_name": "Server Spagna",
        "ping_dir_form_title_new": "Nuovo obiettivo",
        "ping_dir_form_title_edit": "Modifica obiettivo",
        "ping_dir_dlg_del_title": "Elimina",
        "ping_dir_dlg_del_msg": "Eliminare «{name}»?",
    },
    "pt": {
        "ping_dir_title": "Alvos salvos",
        "ping_dir_add_btn": "Adicionar",
        "ping_dir_edit_btn": "Editar",
        "ping_dir_delete_btn": "Eliminar",
        "ping_dir_start_btn": "▶  Monitorar",
        "ping_dir_save_btn": "Guardar",
        "ping_dir_cancel_btn": "Cancelar",
        "ping_dir_save_tooltip": "Guardar no diretório",
        "ping_dir_lbl_name": "Nome:",
        "ping_dir_lbl_host": "Host:",
        "ping_dir_lbl_interval": "Intervalo:",
        "ping_dir_ph_name": "Servidor Espanha",
        "ping_dir_form_title_new": "Novo alvo",
        "ping_dir_form_title_edit": "Editar alvo",
        "ping_dir_dlg_del_title": "Eliminar",
        "ping_dir_dlg_del_msg": "Eliminar «{name}»?",
    },
    "ja": {
        "ping_dir_title": "保存済みターゲット",
        "ping_dir_add_btn": "追加",
        "ping_dir_edit_btn": "編集",
        "ping_dir_delete_btn": "削除",
        "ping_dir_start_btn": "▶  監視開始",
        "ping_dir_save_btn": "保存",
        "ping_dir_cancel_btn": "キャンセル",
        "ping_dir_save_tooltip": "ディレクトリに保存",
        "ping_dir_lbl_name": "名前:",
        "ping_dir_lbl_host": "ホスト:",
        "ping_dir_lbl_interval": "間隔:",
        "ping_dir_ph_name": "スペインのサーバー",
        "ping_dir_form_title_new": "新規ターゲット",
        "ping_dir_form_title_edit": "ターゲットを編集",
        "ping_dir_dlg_del_title": "削除",
        "ping_dir_dlg_del_msg": "「{name}」を削除しますか？",
    },
    "zh": {
        "ping_dir_title": "已保存目标",
        "ping_dir_add_btn": "添加",
        "ping_dir_edit_btn": "编辑",
        "ping_dir_delete_btn": "删除",
        "ping_dir_start_btn": "▶  开始监控",
        "ping_dir_save_btn": "保存",
        "ping_dir_cancel_btn": "取消",
        "ping_dir_save_tooltip": "保存到目录",
        "ping_dir_lbl_name": "名称：",
        "ping_dir_lbl_host": "主机：",
        "ping_dir_lbl_interval": "间隔：",
        "ping_dir_ph_name": "西班牙服务器",
        "ping_dir_form_title_new": "新建目标",
        "ping_dir_form_title_edit": "编辑目标",
        "ping_dir_dlg_del_title": "删除",
        "ping_dir_dlg_del_msg": "删除「{name}」？",
    },
}

lang_order = ["fr", "en", "es", "de", "it", "pt", "ja", "zh"]
lines = content.split("\n")
out = []
lang_idx = 0
for line in lines:
    out.append(line)
    if '"ping_timeout":' in line:
        indent = line[:len(line) - len(line.lstrip())]
        lang = lang_order[lang_idx]
        lang_idx += 1
        for key, val in new_keys[lang].items():
            escaped = val.replace('"', '\\"')
            out.append(f'{indent}"{key}": "{escaped}",')

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("inserted for", lang_idx, "languages")
EOF
```

Expected output: `inserted for 8 languages`

- [ ] **Step 3: Verify all keys resolve in all languages**

```bash
cd ~/claude-projects/nmlinux && python3 -c "
from nmlinux.core.i18n import _T
keys = ['ping_dir_title', 'ping_dir_add_btn', 'ping_dir_edit_btn', 'ping_dir_delete_btn',
        'ping_dir_start_btn', 'ping_dir_save_btn', 'ping_dir_cancel_btn', 'ping_dir_save_tooltip',
        'ping_dir_lbl_name', 'ping_dir_lbl_host', 'ping_dir_lbl_interval', 'ping_dir_ph_name',
        'ping_dir_form_title_new', 'ping_dir_form_title_edit', 'ping_dir_dlg_del_title',
        'ping_dir_dlg_del_msg']
for lang in ['fr','en','es','de','it','pt','ja','zh']:
    for k in keys:
        assert k in _T[lang], f'{k} missing in {lang}'
print('All 16 keys present in all 8 languages')
"
```

Expected: `All 16 keys present in all 8 languages`

- [ ] **Step 4: Byte-compile to catch syntax errors**

Run: `cd ~/claude-projects/nmlinux && python3 -m py_compile nmlinux/core/i18n.py`

Expected: no output, exit code 0

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/nmlinux
git add nmlinux/core/i18n.py
git commit -m "Add i18n keys for Ping Monitor saved targets directory (8 languages)"
```

---

### Task 3: Directory panel UI — list, CRUD form, Start monitoring

**Files:**
- Modify: `nmlinux/pages/ping.py`

**Interfaces:**
- Consumes: `PingTarget`, `_PingTargetStore` from Task 1; `tr()` keys from Task 2; existing `PingPage._add_host(host: str, interval: int) -> None` and `self._workers: dict[str, PingWorker]`.
- Produces: `PingPage._build_directory_panel() -> QWidget`, `PingPage._build_monitor_panel() -> QWidget`, `PingPage._refresh_directory_list() -> None` (used by Task 4).

- [ ] **Step 1: Add new Qt widget imports**

In `nmlinux/pages/ping.py`, replace:

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
```

with:

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QFormLayout, QMessageBox,
)
```

- [ ] **Step 2: Split `_build_ui` into a splitter with directory + monitor panels**

Replace the existing `_build_ui` method:

```python
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("ping_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        bar = QHBoxLayout()

        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("ping_placeholder"))
        self._input.returnPressed.connect(self._on_add)
        self._input.textChanged.connect(self._update_cli)

        self._interval_cb = QComboBox()
        for label, val in [("1 s", 1), ("2 s", 2), ("5 s", 5), ("10 s", 10), ("30 s", 30)]:
            self._interval_cb.addItem(label, val)
        self._interval_cb.setCurrentIndex(1)
        self._interval_cb.currentIndexChanged.connect(self._update_cli)

        btn_add   = QPushButton(tr("ping_add_btn"))
        btn_add.setDefault(True)
        btn_add.clicked.connect(self._on_add)

        btn_clear = QPushButton(tr("ping_clear_btn"))
        btn_clear.clicked.connect(self._on_clear_all)

        bar.addWidget(self._input, 1)
        bar.addWidget(QLabel(tr("ping_interval_lbl")))
        bar.addWidget(self._interval_cb)
        bar.addWidget(btn_add)
        bar.addWidget(btn_clear)
        layout.addLayout(bar)

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels([
            "", tr("ping_col_host"), tr("ping_col_sent"), tr("ping_col_loss"),
            tr("ping_col_last"), tr("common_min"), tr("ping_col_avg"), tr("common_max"), "",
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_C_HOST, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_C_DOT, 28)
        self._table.setColumnWidth(_C_DEL, 36)

        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_right_click)
```

with:

```python
    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_directory_panel())
        splitter.addWidget(self._build_monitor_panel())
        splitter.setSizes([220, 700])
        root.addWidget(splitter)

    def _build_directory_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)
        layout.addWidget(QLabel(tr("ping_dir_title")))

        self._dir_list = QListWidget()
        self._dir_list.setFrameShape(QFrame.Shape.NoFrame)
        self._dir_list.currentRowChanged.connect(self._on_directory_select)
        layout.addWidget(self._dir_list, 1)

        btns = QHBoxLayout()
        self._dir_btn_add    = QPushButton(tr("ping_dir_add_btn"))
        self._dir_btn_edit   = QPushButton(tr("ping_dir_edit_btn"))
        self._dir_btn_delete = QPushButton(tr("ping_dir_delete_btn"))
        self._dir_btn_add.clicked.connect(self._on_directory_new)
        self._dir_btn_edit.clicked.connect(self._on_directory_edit)
        self._dir_btn_delete.clicked.connect(self._on_directory_delete)
        for b in (self._dir_btn_add, self._dir_btn_edit, self._dir_btn_delete):
            btns.addWidget(b)
        layout.addLayout(btns)

        self._dir_form_title = QLabel()
        self._dir_form_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._dir_form_title)

        form = QFormLayout()
        form.setSpacing(4)
        self._dir_f_name = QLineEdit()
        self._dir_f_name.setPlaceholderText(tr("ping_dir_ph_name"))
        self._dir_f_host = QLineEdit()
        self._dir_f_interval = QComboBox()
        for label, val in [("1 s", 1), ("2 s", 2), ("5 s", 5), ("10 s", 10), ("30 s", 30)]:
            self._dir_f_interval.addItem(label, val)
        self._dir_f_interval.setCurrentIndex(1)
        form.addRow(tr("ping_dir_lbl_name"),     self._dir_f_name)
        form.addRow(tr("ping_dir_lbl_host"),     self._dir_f_host)
        form.addRow(tr("ping_dir_lbl_interval"), self._dir_f_interval)
        layout.addLayout(form)

        act = QHBoxLayout()
        self._dir_btn_start  = QPushButton(tr("ping_dir_start_btn"))
        self._dir_btn_save   = QPushButton(tr("ping_dir_save_btn"))
        self._dir_btn_cancel = QPushButton(tr("ping_dir_cancel_btn"))
        self._dir_btn_start.setStyleSheet("font-weight: bold;")
        self._dir_btn_start.clicked.connect(self._on_directory_start)
        self._dir_btn_save.clicked.connect(self._on_directory_save)
        self._dir_btn_cancel.clicked.connect(self._on_directory_cancel)
        act.addWidget(self._dir_btn_start)
        act.addStretch()
        act.addWidget(self._dir_btn_cancel)
        act.addWidget(self._dir_btn_save)
        layout.addLayout(act)

        self._set_directory_form_mode(view=False)
        return panel

    def _build_monitor_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("ping_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        bar = QHBoxLayout()

        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("ping_placeholder"))
        self._input.returnPressed.connect(self._on_add)
        self._input.textChanged.connect(self._update_cli)

        self._interval_cb = QComboBox()
        for label, val in [("1 s", 1), ("2 s", 2), ("5 s", 5), ("10 s", 10), ("30 s", 30)]:
            self._interval_cb.addItem(label, val)
        self._interval_cb.setCurrentIndex(1)
        self._interval_cb.currentIndexChanged.connect(self._update_cli)

        btn_add   = QPushButton(tr("ping_add_btn"))
        btn_add.setDefault(True)
        btn_add.clicked.connect(self._on_add)

        btn_clear = QPushButton(tr("ping_clear_btn"))
        btn_clear.clicked.connect(self._on_clear_all)

        bar.addWidget(self._input, 1)
        bar.addWidget(QLabel(tr("ping_interval_lbl")))
        bar.addWidget(self._interval_cb)
        bar.addWidget(btn_add)
        bar.addWidget(btn_clear)
        layout.addLayout(bar)

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels([
            "", tr("ping_col_host"), tr("ping_col_sent"), tr("ping_col_loss"),
            tr("ping_col_last"), tr("common_min"), tr("ping_col_avg"), tr("common_max"), "", "",
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_C_HOST, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_C_DOT, 28)
        self._table.setColumnWidth(_C_SAVE, 28)
        self._table.setColumnWidth(_C_DEL, 36)

        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_right_click)
        return panel
```

- [ ] **Step 3: Update the column enum for the new ★ column**

Replace:

```python
_C_DOT, _C_HOST, _C_SENT, _C_LOSS, _C_LAST, _C_MIN, _C_AVG, _C_MAX, _C_DEL = range(9)
```

with:

```python
_C_DOT, _C_HOST, _C_SENT, _C_LOSS, _C_LAST, _C_MIN, _C_AVG, _C_MAX, _C_SAVE, _C_DEL = range(10)
```

(The `_C_SAVE` column itself is populated in Task 4 — this task only reserves the column and header cell so the layout is correct.)

- [ ] **Step 4: Initialize the store and directory state in `__init__`**

Replace:

```python
    def __init__(self) -> None:
        super().__init__()
        self._workers: dict[str, PingWorker] = {}
        self._stats:   dict[str, _Stats]     = {}
        self._rows:    dict[str, int]         = {}
        self._build_ui()
```

with:

```python
    def __init__(self) -> None:
        super().__init__()
        self._workers: dict[str, PingWorker] = {}
        self._stats:   dict[str, _Stats]     = {}
        self._rows:    dict[str, int]         = {}
        self._target_store = _PingTargetStore()
        self._dir_editing: int | None = None
        self._build_ui()
        self._refresh_directory_list()
```

- [ ] **Step 5: Add directory CRUD + Start monitoring methods**

Add these methods to `PingPage` (e.g. after `_on_stop`... there is no `_on_stop` in this file; add them right after `_update_cli` and before `_on_add`):

```python
    # ── Directory ────────────────────────────────────────────────────────────

    def _refresh_directory_list(self) -> None:
        current = self._dir_list.currentRow()
        self._dir_list.clear()
        for t in self._target_store.all():
            label = f"{t.name}  —  {t.host}" if t.name else t.host
            self._dir_list.addItem(QListWidgetItem(label))
        if 0 <= current < self._dir_list.count():
            self._dir_list.setCurrentRow(current)

    def _on_directory_select(self, row: int) -> None:
        if row < 0:
            return
        self._dir_editing = row
        self._load_directory_form(self._target_store.all()[row])
        self._set_directory_form_mode(view=True)

    def _on_directory_new(self) -> None:
        self._dir_editing = None
        self._dir_list.clearSelection()
        self._load_directory_form(PingTarget())
        self._set_directory_form_mode(view=False)
        self._dir_form_title.setText(tr("ping_dir_form_title_new"))
        self._dir_f_name.setFocus()

    def _on_directory_edit(self) -> None:
        if self._dir_editing is None:
            return
        self._set_directory_form_mode(view=False)
        self._dir_form_title.setText(tr("ping_dir_form_title_edit"))

    def _on_directory_delete(self) -> None:
        row = self._dir_list.currentRow()
        if row < 0:
            return
        t = self._target_store.all()[row]
        name = t.name or t.host
        ans = QMessageBox.question(
            self, tr("ping_dir_dlg_del_title"), tr("ping_dir_dlg_del_msg", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self._target_store.remove(row)
            self._dir_editing = None
            self._refresh_directory_list()
            self._clear_directory_form()

    def _on_directory_save(self) -> None:
        host = self._dir_f_host.text().strip()
        if not host:
            return
        t = PingTarget(
            name     = self._dir_f_name.text().strip(),
            host     = host,
            interval = self._dir_f_interval.currentData(),
        )
        if self._dir_editing is None:
            self._target_store.add(t)
            self._dir_editing = len(self._target_store.all()) - 1
        else:
            self._target_store.update(self._dir_editing, t)
        self._refresh_directory_list()
        self._dir_list.setCurrentRow(self._dir_editing)
        self._set_directory_form_mode(view=True)

    def _on_directory_cancel(self) -> None:
        if self._dir_editing is not None:
            self._load_directory_form(self._target_store.all()[self._dir_editing])
            self._set_directory_form_mode(view=True)
        else:
            self._clear_directory_form()

    def _on_directory_start(self) -> None:
        if self._dir_editing is None:
            return
        t = self._target_store.all()[self._dir_editing]
        if t.host in self._workers:
            return
        self._add_host(t.host, t.interval)
        self._set_directory_form_mode(view=True)

    def _load_directory_form(self, t: PingTarget) -> None:
        self._dir_f_name.setText(t.name)
        self._dir_f_host.setText(t.host)
        idx = self._dir_f_interval.findData(t.interval)
        self._dir_f_interval.setCurrentIndex(idx if idx >= 0 else 1)

    def _clear_directory_form(self) -> None:
        self._dir_editing = None
        self._dir_f_name.clear()
        self._dir_f_host.clear()
        self._dir_f_interval.setCurrentIndex(1)
        self._dir_form_title.setText("")

    def _set_directory_form_mode(self, *, view: bool) -> None:
        self._dir_f_name.setReadOnly(view)
        self._dir_f_host.setReadOnly(view)
        self._dir_f_interval.setEnabled(not view)
        self._dir_btn_start.setVisible(view)
        self._dir_btn_save.setVisible(not view)
        self._dir_btn_cancel.setVisible(not view)
        if view and self._dir_editing is not None:
            t = self._target_store.all()[self._dir_editing]
            self._dir_form_title.setText(t.name or t.host)
            self._dir_btn_start.setEnabled(t.host not in self._workers)
```

- [ ] **Step 6: Byte-compile to catch syntax errors**

Run: `cd ~/claude-projects/nmlinux && python3 -m py_compile nmlinux/pages/ping.py`

Expected: no output, exit code 0

- [ ] **Step 7: Headless smoke test of the directory CRUD flow**

```bash
cd ~/claude-projects/nmlinux && QT_QPA_PLATFORM=offscreen python3 -c "
from PySide6.QtWidgets import QApplication
from nmlinux.pages.ping import PingPage, PingTarget

app = QApplication.instance() or QApplication([])
page = PingPage()

# New target via the directory form
page._on_directory_new()
page._dir_f_name.setText('Spain DNS')
page._dir_f_host.setText('8.8.8.8')
page._on_directory_save()
assert page._target_store.all() == [PingTarget(name='Spain DNS', host='8.8.8.8', interval=2)]
assert page._dir_list.count() == 1
print('add: OK')

# Edit it
page._dir_list.setCurrentRow(0)
page._on_directory_edit()
page._dir_f_name.setText('Spain DNS (edited)')
page._on_directory_save()
assert page._target_store.all()[0].name == 'Spain DNS (edited)'
print('edit: OK')

# Start monitoring from the directory
page._dir_list.setCurrentRow(0)
assert '8.8.8.8' not in page._workers
page._on_directory_start()
assert '8.8.8.8' in page._workers
print('start: OK')

# Delete
page._on_clear_all()
print('ALL OK')
"
```

Expected: `add: OK`, `edit: OK`, `start: OK`, `ALL OK` — no tracebacks. (Note: `_on_directory_delete` uses a modal `QMessageBox`, not exercised here since it blocks; it's covered visually in Task 5.)

- [ ] **Step 8: Run the full test suite to check for regressions**

Run: `cd ~/claude-projects/nmlinux && python3 -m pytest tests/ -q`

Expected: all tests pass, no failures

- [ ] **Step 9: Commit**

```bash
cd ~/claude-projects/nmlinux
git add nmlinux/pages/ping.py
git commit -m "Add saved targets directory panel to Ping Monitor"
```

---

### Task 4: ★ save-to-directory button on live monitoring rows

**Files:**
- Modify: `nmlinux/pages/ping.py`

**Interfaces:**
- Consumes: `_C_SAVE` column index and `_PingTargetStore` from Task 3; `PingPage._refresh_directory_list()` from Task 3.
- Produces: `PingPage._on_save_to_directory(host: str, interval: int) -> None`.

- [ ] **Step 1: Add the ★ button when a row is created**

In `_add_host`, replace:

```python
        btn = QPushButton("✕")
        btn.setFixedWidth(28)
        btn.clicked.connect(lambda _checked=False, h=host: self._on_remove(h))
        self._table.setCellWidget(row, _C_DEL, btn)
```

with:

```python
        btn_save = QPushButton("★")
        btn_save.setFixedWidth(28)
        btn_save.setToolTip(tr("ping_dir_save_tooltip"))
        btn_save.setEnabled(not self._target_store.has_host(host))
        btn_save.clicked.connect(
            lambda _checked=False, h=host, i=interval: self._on_save_to_directory(h, i)
        )
        self._table.setCellWidget(row, _C_SAVE, btn_save)

        btn = QPushButton("✕")
        btn.setFixedWidth(28)
        btn.clicked.connect(lambda _checked=False, h=host: self._on_remove(h))
        self._table.setCellWidget(row, _C_DEL, btn)
```

- [ ] **Step 2: Implement `_on_save_to_directory`**

Add this method next to `_on_remove`:

```python
    def _on_save_to_directory(self, host: str, interval: int) -> None:
        if self._target_store.has_host(host):
            return
        self._target_store.add(PingTarget(name='', host=host, interval=interval))
        self._refresh_directory_list()
        row = self._rows.get(host)
        if row is not None:
            btn = self._table.cellWidget(row, _C_SAVE)
            if btn:
                btn.setEnabled(False)
```

- [ ] **Step 3: Byte-compile to catch syntax errors**

Run: `cd ~/claude-projects/nmlinux && python3 -m py_compile nmlinux/pages/ping.py`

Expected: no output, exit code 0

- [ ] **Step 4: Headless smoke test of save-from-active-row**

```bash
cd ~/claude-projects/nmlinux && QT_QPA_PLATFORM=offscreen python3 -c "
from PySide6.QtWidgets import QApplication
from nmlinux.pages.ping import PingPage, _C_SAVE

app = QApplication.instance() or QApplication([])
page = PingPage()

page._add_host('1.1.1.1', 2)
assert page._target_store.all() == []
row = page._rows['1.1.1.1']
btn = page._table.cellWidget(row, _C_SAVE)
assert btn.isEnabled()
btn.click()

assert page._target_store.has_host('1.1.1.1')
assert not btn.isEnabled()
print('save-from-row: OK')

# Adding another row for the same host now already in the directory should
# start with the star button disabled
page._on_remove('1.1.1.1')
page._add_host('1.1.1.1', 2)
row2 = page._rows['1.1.1.1']
btn2 = page._table.cellWidget(row2, _C_SAVE)
assert not btn2.isEnabled()
print('duplicate-guard: OK')

page._on_clear_all()
print('ALL OK')
"
```

Expected: `save-from-row: OK`, `duplicate-guard: OK`, `ALL OK` — no tracebacks.

- [ ] **Step 5: Run the full test suite to check for regressions**

Run: `cd ~/claude-projects/nmlinux && python3 -m pytest tests/ -q`

Expected: all tests pass, no failures

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/nmlinux
git add nmlinux/pages/ping.py
git commit -m "Add save-to-directory button on active Ping Monitor rows"
```

---

### Task 5: End-to-end headless verification (screenshot)

**Files:**
- None modified — this task only verifies Tasks 1-4 together, exactly as done for the Asset Inventory feature earlier in this project (same `QT_QPA_PLATFORM=offscreen` + `page.show()` + `page.grab().save(...)` method).

**Interfaces:**
- Consumes: everything produced by Tasks 1-4. No new interfaces produced.

- [ ] **Step 1: Write and run the end-to-end script**

```bash
mkdir -p /tmp/nmlinux_verify
cd ~/claude-projects/nmlinux && QT_QPA_PLATFORM=offscreen python3 -c "
from PySide6.QtWidgets import QApplication
from nmlinux.pages.ping import PingPage

app = QApplication.instance() or QApplication([])
page = PingPage()
page.resize(1000, 500)
page.show()

# 1. Add a target straight to the directory (pre-planning use case)
page._on_directory_new()
page._dir_f_name.setText('Spain DNS')
page._dir_f_host.setText('8.8.8.8')
page._on_directory_save()

# 2. Start monitoring an ad hoc host via the quick-add field (existing flow)
page._input.setText('1.1.1.1')
page._on_add()

# 3. Save that ad hoc host into the directory mid-session (the actual bug fix)
row = page._rows['1.1.1.1']
page._table.cellWidget(row, 8).click()  # _C_SAVE column index

app.processEvents()
assert page._dir_list.count() == 2, f'expected 2 directory entries, got {page._dir_list.count()}'
assert page._target_store.has_host('8.8.8.8')
assert page._target_store.has_host('1.1.1.1')
print('directory has both entries: OK')

page.grab().save('/tmp/nmlinux_verify/ping_directory.png')
print('screenshot saved')
"
```

Expected: `directory has both entries: OK` and `screenshot saved`, no tracebacks.

- [ ] **Step 2: View the screenshot**

Read `/tmp/nmlinux_verify/ping_directory.png` (e.g. with the `Read` tool) and confirm visually:
- A left directory panel is present with 2 entries listed (`Spain DNS  —  8.8.8.8` and `1.1.1.1`)
- The right panel still shows the original quick-add toolbar and the live monitoring table with a row for `1.1.1.1`
- The ★ button on that row appears disabled (since it was just saved to the directory)

If anything looks wrong (misaligned columns, missing labels, overlapping widgets), fix it in the relevant file from Task 3/4 before proceeding — do not mark this task done on a broken screenshot.

- [ ] **Step 3: Run the full test suite one final time**

Run: `cd ~/claude-projects/nmlinux && python3 -m pytest tests/ -q`

Expected: all tests pass, no failures

- [ ] **Step 4: Clean up the verification artifact**

```bash
rm -rf /tmp/nmlinux_verify
```

(No commit for this task — it modifies no tracked files, it only verifies Tasks 1-4 working together.)

---

## Self-Review

**Spec coverage:**
- Data model (`PingTarget`, `_PingTargetStore`) → Task 1 ✓
- i18n keys → Task 2 ✓
- Directory panel UI (list, add/edit/delete, form, splitter restructure) → Task 3 ✓
- "Start monitoring" button with duplicate guard → Task 3 ✓
- ★ save-to-directory button with duplicate guard → Task 4 ✓
- Quick-add field stays ephemeral/unchanged → verified implicitly (Task 3 moves it into `_build_monitor_panel` unmodified; Task 5 exercises it still works)
- Error handling (corrupt JSON → empty list) → Task 1 test `test_load_corrupt_json_returns_empty_list`
- Headless verification with screenshot → Task 5 ✓

**Placeholder scan:** no TBD/TODO; every step has complete code, exact commands, and expected output.

**Type consistency:** `PingTarget(name, host, interval)` and `_PingTargetStore(path)` signatures are identical across Tasks 1, 3, 4, and 5. Column enum `_C_SAVE` introduced in Task 3 is consumed with the same meaning in Task 4. `_add_host(host, interval)` signature (pre-existing) is unchanged and consumed correctly in Task 3's `_on_directory_start`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-04-ping-monitor-directory.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
