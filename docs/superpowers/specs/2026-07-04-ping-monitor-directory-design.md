# Ping Monitor — saved targets directory

## Problem

`PingPage` (`nmlinux/pages/ping.py`) has no persistence at all: monitored
hosts live only in three in-memory dicts (`_workers`, `_stats`, `_rows`).
If the app closes for any reason — crash, accidental quit, restart — every
monitored host is lost and must be retyped from scratch.

This surfaced concretely when the user was troubleshooting a connectivity
issue to Spain and had three IPs running in the Ping Monitor; closing the
app for an unrelated reason lost all three.

## Goal

Add a manually-curated directory of saved ping targets, following the
existing "simple saved list" pattern already used by Wake on LAN
(`nmlinux/pages/wol.py`) — a flat `QListWidget` backed by a JSON file, no
groups/tree (that's the SSH module's heavier pattern, explicitly not wanted
here).

Directory entries are added deliberately (via a small form, like WoL) or
by saving a host that's *already* being monitored (via a new per-row save
button). Starting monitoring from a saved entry is a manual action
(double-click / button) — the app does not auto-resume monitoring on
launch. This was an explicit choice: the user picked "manual directory"
over "auto-resume active session" when offered both.

## Non-goals

- No automatic restore of the live monitoring session on app launch.
- No groups/folders (unlike SSH) — a flat list is enough for this use case.
- No change to the existing quick-add text field behavior — it stays
  ephemeral/one-off, exactly as today.

## Data model

New dataclass and store, colocated in `nmlinux/pages/ping.py` (matching
where `wol.py` keeps its equivalents — this module is small enough that a
separate `core/` file isn't warranted):

```python
@dataclass
class PingTarget:
    name:     str = ''
    host:     str = ''
    interval: int = 2   # seconds; one of the existing combo values (1/2/5/10/30)


class _PingTargetStore:
    def __init__(self) -> None: ...          # loads from _STORE_PATH
    def all(self) -> list[PingTarget]: ...
    def add(self, target: PingTarget) -> None: ...
    def update(self, idx: int, target: PingTarget) -> None: ...
    def remove(self, idx: int) -> None: ...
```

Storage path: `~/.local/share/nmlinux/ping_targets.json`, same directory
convention as `wol_hosts.json` and `ssh_connections.json`. Plain JSON list
of objects (`[asdict(t) for t in targets]`), no version field needed (flat
list, no legacy format to migrate — unlike SSH's v1→v2 groups migration).

## UI layout

`PingPage._build_ui` is restructured from a single `QVBoxLayout` into a
`QHBoxLayout` + `QSplitter(Qt.Orientation.Horizontal)`, matching the
`wol.py`/`ssh.py` convention:

- **Left panel** (new) — directory:
  - `QLabel` title
  - `QListWidget` showing `"{name} — {host}"` (or just `host` if no name),
    same label format as WoL
  - Add / Edit / Delete buttons below the list
  - A small inline form (name, host, interval combo) shown in
    add/edit mode — reusing the same view/edit toggle pattern as
    `WolPage._set_form_mode`
  - A "Start monitoring" button, shown once a saved entry is selected
    (single click, exactly like WoL's select → view-mode-with-Wake-button
    pattern — no double-click). Calls the existing `_add_host()` with the
    entry's host + interval. If that host is already being monitored
    (already a key in `self._workers`), the button is disabled instead of
    creating a duplicate row (same guard `_on_add` already has).

- **Right panel** (existing, unchanged) — the current top toolbar
  (quick-add field, interval combo, Add/Clear buttons) plus the live
  monitoring table.

- **New**: a ★ (save) button in a new dedicated column
  (`_C_SAVE`, inserted right before the existing `_C_DEL` column — the
  column tuple becomes `_C_DOT, _C_HOST, _C_SENT, _C_LOSS, _C_LAST,
  _C_MIN, _C_AVG, _C_MAX, _C_SAVE, _C_DEL = range(10)`) on each row of the
  live monitoring table. Clicking it creates a `PingTarget(host=<row
  host>, interval=<row's configured interval>)` and calls
  `_PingTargetStore.add(...)`, then refreshes the directory list. If the
  host is already present in the store (matched by `host` string), the
  button is disabled/hidden for that row instead of creating a duplicate
  entry.

Splitter sizes default to `[220, 700]`, matching `ssh.py`'s and roughly
`wol.py`'s proportions.

## Interaction flow

1. **Ad hoc, as today**: type a host in the quick-add field → Enter/Add →
   starts monitoring, nothing persisted.
2. **Save from an active row**: click ★ on a monitored row → host is
   added to the directory (interval taken from that row's current
   interval). Solves the original problem: user can save mid-session,
   before closing the app, without having pre-planned it.
3. **Add directly to the directory** (not yet monitoring): use the
   directory's own Add button → small form (name/host/interval) → Save →
   entry appears in the list, not yet monitored.
4. **Resume after restart**: open Ping Monitor, directory list is
   populated from disk (loaded in `PingPage.__init__` like WoL does),
   select an entry (single click, populates the view-mode form), click
   "Start monitoring" → host is added to the live table via the existing
   `_add_host()` path.
5. **Edit / Delete**: standard, mirrors WoL exactly (select row → Edit
   loads form → Save calls `store.update(idx, ...)`; Delete asks for
   confirmation via `QMessageBox`, same as WoL's delete confirmation).

Directory entries are edited independently from live monitoring rows —
editing a saved target's interval does not affect a row that's currently
running with a different interval (they're decoupled once monitoring has
started, exactly like WoL: editing a saved host doesn't affect a magic
packet already sent).

## Error handling

- Store load failures (corrupt JSON) fall back to an empty list, silently
  — same behavior as `_WolStore._load` and `SshStore.load`. No dialog,
  no crash; user can just re-add entries.
- Duplicate prevention: both the ★ save button and the "Start monitoring"
  button guard against the host already being present (in the store, or
  in the live `_workers` dict respectively) rather than raising an error —
  consistent with `_on_add`'s existing silent no-op for a host already
  being monitored.
- No input validation beyond "non-empty host" is needed for save/add —
  the existing `_add_host()` already handles unreachable/invalid hosts
  gracefully (ping just fails, row shows timeout status).

## Testing

`nmlinux/pages/ping.py` currently has no dedicated test file. Following
the project convention (see `tests/test_ssh_keys.py`, or more precisely
the pure-logic split used for other modules), the new `PingTarget` /
`_PingTargetStore` pair is plain Python with no Qt dependency in its
logic (like `WolHost`/`_WolStore`), so it's directly unit-testable without
a `QApplication`:

- `tests/test_ping_targets.py`:
  - store round-trip (add → all() returns it; save → reload from a fresh
    store instance → same data)
  - update() replaces the entry at the given index
  - remove() deletes the entry at the given index
  - load() on a missing file returns an empty list (no crash)
  - load() on corrupt JSON returns an empty list (no crash)

UI wiring (splitter layout, ★ button, Start monitoring button, duplicate
guards) is verified by driving the real page headlessly
(`QT_QPA_PLATFORM=offscreen`), the same method established in the Asset
Inventory session on 2026-07-04: instantiate `PingPage`, call `show()`,
exercise the new buttons programmatically, and grab a screenshot for
visual confirmation.

## Files touched

- `nmlinux/pages/ping.py` — `PingTarget`, `_PingTargetStore`, splitter
  restructure, ★ button, directory panel, "Start monitoring" button
- `nmlinux/core/i18n.py` — new keys for the directory panel (title, Add/
  Edit/Delete/Start button labels, form placeholders), 8 languages
- `tests/test_ping_targets.py` — new
