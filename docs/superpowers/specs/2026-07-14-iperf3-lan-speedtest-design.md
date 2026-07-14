# iperf3 LAN tab (Speed Test) — Design Spec
Date: 2026-07-14

## Overview

Add iperf3 support to the existing **Speed Test** module as a second tab,
alongside the current "Internet" (curl + Cloudflare, DT-08) test. The new
"LAN" tab measures throughput against a user-chosen iperf3 server — either a
saved organization/custom server, or one picked from a bundled list of public
iperf3 servers by country.

Origin: GitHub issue #6 (`loren2018tw`, opened 2026-07-08). Confirmed use
cases (issue comments, 2026-07-14):
- Fixed internal iperf3 server within the user's organization
- Bundled list of public iperf3 servers by country, to test international
  bandwidth
- IPv4 vs IPv6 throughput comparison

Decision (2026-07-14, made by nmlinux maintainer without waiting for further
issue back-and-forth):
- **Client only.** iperf3 server mode (nmlinux acting as an iperf3 target for
  another LAN host) is deferred — see [Out of Scope](#out-of-scope).
- **Tab inside Speed Test**, not a new module/sidebar entry — iperf3 LAN
  testing is framed as a complement to the existing internet test, matching
  Loren's own framing ("Internet" vs "LAN").

## Constraints

- `iperf3` is an optional system dependency (not always installed) — same
  graceful-degradation pattern as `curl`/`_CMD_CURL` in the existing module:
  detect via `shutil.which`, disable Start + show a banner if absent.
- Client mode only: `iperf3 -c <host> ...`. Never spawn `iperf3 -s`.
- One test at a time, same as the Internet tab (`SpeedTestWorker` pattern).
- Public server list is bundled read-only data shipped with the app; user's
  own servers (org server, home lab, etc.) are a separate, editable, persisted
  list — same split as "predefined" vs "user-managed" seen nowhere else yet in
  nmlinux, closest precedent is `PingTarget`'s saved-targets directory
  (`ping_targets.json`, `nmlinux/pages/ping.py`).
- No credentials involved (public iperf3 servers require none; an org server
  behind auth is out of scope for iperf3 itself).

## Architecture

### Worker — `Iperf3Worker(QThread)`

Same shape as `SpeedTestWorker` (`nmlinux/pages/speedtest.py:48`): a `QThread`
subclass with typed `Signal`s, spawns `iperf3` via `subprocess.Popen`, parses
`-J` (JSON) output, never blocks the UI thread.

```python
class Iperf3Worker(QThread):
    result_ready = Signal(dict)   # parsed summary, see below
    error        = Signal(str)
    finished     = Signal()

    def __init__(self, host: str, port: int, *, udp: bool, ip_mode: str,
                 reverse: bool, duration: int) -> None: ...
```

Command construction:

```
iperf3 -c <host> -p <port> -J -t <duration>
       [-u]                 # udp
       [-4 | -6]            # ip_mode in {"4", "6"}; omit flag for "auto"
       [-R]                 # reverse = download direction
```

- Default `duration`: 10s (matches typical iperf3 default; keep test short by
  default, same spirit as the 25 MB/10 MB caps in the Internet tab).
- Timeout for `communicate()`: `duration + 15` seconds (leaves margin for
  connection setup / slow server).
- `-J` output parsed with `json.loads`; on non-zero exit or parse failure,
  emit `error` with the raw `stderr` (iperf3 prints human-readable errors
  there — e.g. "unable to connect to server", "the client and server are
  running different versions").

Result dict (from JSON `end` section):

```python
{
    'sent_mbps':     ...,   # end.sum_sent.bits_per_second / 1_000_000
    'received_mbps': ...,   # end.sum_received.bits_per_second / 1_000_000 (TCP)
                             # or end.sum.bits_per_second (UDP)
    'jitter_ms':     ... | None,   # end.sum.jitter_ms (UDP only)
    'loss_pct':      ... | None,   # end.sum.lost_percent (UDP only)
    'ip_version':    '4' | '6',    # actually used, read back from JSON `start.connected[0].local_host`
}
```

TCP reports both `sum_sent` and `sum_received` (retransmits can make them
differ). UDP reports a single `sum` with jitter/loss — no separate
sent/received split. The worker normalizes both into the dict above,
`jitter_ms`/`loss_pct` staying `None` for TCP.

### Server list — bundled public servers + saved custom servers

**Bundled (read-only):** `nmlinux/assets/iperf3_public_servers.json`, shipped
with the package (same mechanism as `nmlinux/assets/world.geojson` for
Topology). Format:

```json
[
  {"country": "FR", "name": "Bouygues Telecom", "host": "bouygues.iperf.fr", "port": 5201},
  {"country": "US", "name": "...", "host": "...", "port": 5201}
]
```

Sourced from community-maintained public lists (e.g. iperf.fr's server list,
`R0GGER/public-iperf3-servers` on GitHub) — **exact entries to be verified for
liveness at implementation time**, not guessed in this spec. Country grouped
in a `QComboBox` (country) → `QComboBox` (server within country), mirroring
no existing nmlinux pattern exactly but simple enough to need no new
abstraction.

**Custom (user-managed, persisted):** `~/.local/share/nmlinux/iperf3_servers.json`,
same dataclass + JSON list pattern as `PingTarget` (`nmlinux/pages/ping.py`):

```python
@dataclass
class Iperf3Server:
    name: str
    host: str
    port: int = 5201
```

UI: a `QListWidget` of saved servers (name shown, host:port as tooltip) with
add/remove buttons — reuse the add/remove interaction from the ping targets
directory rather than inventing a new one.

### Radio choice: Public list vs Custom

A `QButtonGroup` of two radios switches which selector is active:
- **Public list**: country combo + server combo (from bundled JSON)
- **Custom / saved**: host/port line edits + saved-servers list to pick from,
  with a "★ Save" button to persist the currently-entered host/port

## UI Layout

```
┌─ Speed Test ──────────────────────────────────────────────────────┐
│ [ Internet ]  [ LAN (iperf3) ]                                     │
├──────────────────────────────────────────────────────────────────┤
│  Server:  (•) Public list   [ Country: France ▾] [ Server: Bouygues ▾]│
│           ( ) Custom        [ host________ ] [port 5201]  [★ Save]  │
│           Saved: [ MonServeurOrg ▾ ]                        [🗑]    │
│                                                                      │
│  Protocol: (•) TCP  ( ) UDP     IP: (•) Auto  ( ) IPv4  ( ) IPv6    │
│  Direction: [ ] Reverse (download)     Duration: [ 10s ▾ ]         │
│                                                                      │
│  [ ▶ Start ]  [ ■ Stop ]                     <status label>        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (indeterminate progress bar while running)   │
│                                                                      │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│   │  SENT    │   │ RECEIVED │   │  JITTER  │   │   LOSS   │        │
│   │  941.2   │   │  938.7   │   │   0.31   │   │   0.00   │        │
│   │  Mbit/s  │   │  Mbit/s  │   │    ms    │   │    %     │        │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│  (jitter/loss cards hidden unless UDP was used)                    │
└──────────────────────────────────────────────────────────────────┘
```

- Reuses `_MetricCard` from the same file for the 4 result cards.
- Reuses the Start/Stop/progress-bar/status-label pattern from the Internet
  tab (`_btn_start`, `_btn_stop`, `_progress`, `_lbl_status` — one instance
  per tab, not shared, to allow independent state).
- No history graph for the LAN tab in v1 — a single server/protocol/duration
  combination doesn't compose into a meaningful trend line the way "my
  internet speed over time" does. Can be revisited if requested.

## Files to Create / Modify

| File | Action |
|------|--------|
| `nmlinux/pages/speedtest.py` | Modify — wrap existing UI in `QTabWidget` as tab 1 ("Internet"), add `_LanSpeedTab` widget as tab 2 ("LAN"), add `Iperf3Worker` |
| `nmlinux/assets/iperf3_public_servers.json` | Create — bundled public server list |
| `nmlinux/core/i18n.py` | Modify — add `speed_lan_*` keys, all 8 languages |
| `docs/Carte-des-Modules.md` | Modify — update Speed Test module section |
| `docs/Decisions-Techniques.md` | Modify — new DT entry: iperf3 client-only + tab-not-module rationale |
| `docs/Roadmap.md` | Modify — move iperf3 candidate to delivered once shipped |
| `CLAUDE.md` §7 | Modify — add `iperf3` to optional system dependencies |
| `tests/test_speedtest_iperf3.py` | Create — parse logic for TCP/UDP JSON, server persistence load/save |

No new sidebar entry, no `window.py` change (Speed Test page already
registered).

## i18n Keys (prefix `speed_lan_`)

All 8 languages: FR, EN, ES, DE, IT, PT, JA, ZH.

```
speed_lan_tab_label, speed_internet_tab_label
speed_lan_server_public, speed_lan_server_custom
speed_lan_lbl_country, speed_lan_lbl_server, speed_lan_lbl_host, speed_lan_lbl_port
speed_lan_btn_save_server, speed_lan_lbl_saved, speed_lan_btn_delete_server
speed_lan_protocol_tcp, speed_lan_protocol_udp
speed_lan_ip_auto, speed_lan_ip_v4, speed_lan_ip_v6
speed_lan_lbl_reverse, speed_lan_lbl_duration
speed_lan_lbl_sent, speed_lan_lbl_received, speed_lan_lbl_jitter, speed_lan_lbl_loss
speed_lan_status_running, speed_lan_status_stop
speed_lan_err_no_cmd, speed_lan_err_connect, speed_lan_err_generic
speed_lan_no_server_selected
```

## Dependencies

- `iperf3` (system binary, not a Python package) — add to CLAUDE.md §7
  optional dependencies, alongside `nmap`, `mtr`, etc. No `pyproject.toml`
  change needed (nothing to add to Python `dependencies`).

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| `iperf3` not installed | Start button disabled, banner shown (same as `_CMD_CURL` check today) |
| No server selected (empty custom host, or public list not yet chosen) | Start button disabled or inline validation message, no subprocess spawned |
| Connection refused / unreachable | `iperf3` exits non-zero, stderr surfaced via `error` signal → status label |
| Different iperf3 protocol versions client/server | Same path — iperf3's own stderr message is descriptive enough to show as-is |
| User clicks Stop mid-test | `terminate()` the subprocess, same as `SpeedTestWorker.stop()` |
| Custom server saved with duplicate name | Overwrite silently (same permissiveness as ping targets — no uniqueness enforced there either) |

## Out of Scope

- **iperf3 server mode** (nmlinux listening for incoming iperf3 tests from
  other LAN hosts). Deferred to a future roadmap item once there's a
  concrete request — running a long-lived listening service changes the
  security/firewall surface of the app in a way client-only mode doesn't,
  and deserves its own spec.
- Editing/removing entries from the *bundled* public server list from the UI
  (only custom/saved servers are user-editable).
- Automatic liveness-check / ping of public servers before listing them —
  v1 just lists them; a stale entry fails the same way any unreachable
  custom host does.
- Result history graph for the LAN tab (see UI Layout note above).
