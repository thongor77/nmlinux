# Asset Inventory: right-click refresh + SSH auth-failure feedback

## Context

Two independent small improvements to the Asset Inventory page, requested after
real-world use:

1. Rescanning a single already-scanned host currently requires re-running a
   full scan (or using the "refresh empty" button, which only covers hosts
   that returned *no* data at all).
2. When a Mac was scanned with the wrong SSH password, the row silently fell
   back to bare Nmap output with no indication that SSH was even attempted —
   the user only realized the password was wrong after independent
   investigation.

## 1. Right-click "Refresh" (multi-selection)

`QTableWidget` already defaults to `ExtendedSelection`, and the table is set
to `SelectRows`, so Ctrl/Shift-click multi-row selection already works with
no changes.

Changes to `nmlinux/pages/asset_inventory.py`:

- Enable a custom context menu on `self._table`
  (`Qt.ContextMenuPolicy.CustomContextMenu` +
  `customContextMenuRequested`).
- Handler: if the row under the cursor is not part of the current selection,
  select that row alone (standard list-widget UX); otherwise keep the
  existing multi-selection.
- Build a local `QMenu` with a single action, labelled via new i18n key
  `inv_ctx_refresh` ("Refresh selected"). This is a page-local menu, not the
  shared `HostActionMenu` from `nmlinux/core/host_actions.py` — that
  component is built for single-IP "send this host to another tool" actions
  and doesn't support multi-selection or in-place rescanning, which is what
  this feature needs.
- On trigger: collect the IP text from `_COL_IP` for every selected row
  (dedup via a set, preserve table order), then call
  `self._start_scan(ips, clear=False)`. This reuses the existing scan
  pipeline verbatim — same worker, same credentials already entered in the
  form.

### Row de-duplication fix (required)

`_on_host` currently always does `self._table.insertRow(row)`. Refreshing an
IP that's already in the table would therefore create a duplicate row.

Fix: before inserting, scan the `_COL_IP` column for a matching IP
(`_find_row_by_ip`), and update that row's cells in place if found, otherwise
insert as today. This is a small linear scan (table sizes are at most a few
hundred rows), safe to run per completed host from the `host_found` signal
handler. It also strengthens the existing "refresh empty" button for free
(no behavior change there since those IPs never had a row).

## 2. SSH auth-failure feedback

`nmlinux/core/asset_collectors.py`:

- `_collect_ssh` (currently returns `{}` when every credential set fails to
  connect) is changed to mirror `_collect_winrm`'s existing behavior: if at
  least one credential set had a non-empty `user` but none of them passed
  `_ssh_connects`, return `{'method': 'SSH', 'error': 'SSH auth failed'}`
  instead of `{}`. If no credential set had a `user` at all (SSH not
  configured for this scan), keep returning `{}` — unchanged, since SSH was
  never actually attempted.
- No UI changes needed: `_on_host` in `asset_inventory.py` already renders
  `asset.get('error')` in the OS column in preference to `asset.get('os')`
  (line ~416), because this exact path already exists for WinRM failures.
- The error string stays a plain, untranslated literal, consistent with how
  WinRM failures already surface raw (untranslated) exception text.

Combined with feature 1, a user who fixes a wrong password can right-click →
refresh the affected row(s) and see the corrected data replace the error in
place.

## Testing

- `tests/test_asset_collectors.py`: new test monkeypatching `_ssh_connects`
  to always return `False`, asserting `_collect_ssh` returns the
  `SSH auth failed` error dict when creds with a `user` are supplied, and
  still returns `{}` when no creds have a `user`.
- `tests/test_asset_inventory.py` (new or extended): direct `QTableWidget`/
  `AssetInventoryPage` test (pattern from `test_host_actions.py` /
  `test_smb_nfs_mount_ui.py`) verifying `_on_host` updates an existing row
  in place for a repeated IP instead of inserting a duplicate.
- Manual verification on a real LAN (right-click → refresh, and a real wrong
  → corrected SSH password cycle) is left to the user, as with prior
  Asset Inventory work — no live hosts available in this environment.

## i18n

New key `inv_ctx_refresh` added to all 8 language blocks in
`nmlinux/core/i18n.py` (fr, en, es, de, it, pt, ja, zh), following the
existing `inv_*` key pattern.
