# NMLinux · v1.3.5

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?business=JFQGY7NU3ANCN&no_recurring=0&item_name=Every+donation%2C+no+matter+how+small%2C+helps+me+keep+this+project+alive.+Thank+you%21%0A&currency_code=EUR)

**A free Linux adaptation of [NETworkManager](https://github.com/BornToBeRoot/NETworkManager) by BornToBeRoot.**

NMLinux brings the spirit of NETworkManager to Linux desktops, reimplemented from scratch in Python and PySide6 (Qt 6). It is not a port of the original C# code, but an independent project inspired by the same idea: a single, unified GUI for the most common network tools a sysadmin or power user needs.

> [!NOTE]
> **NMLinux is not related to the Linux system daemon `/usr/bin/NetworkManager` (NetworkManager by Red Hat/GNOME).** The name comes from [NETworkManager](https://github.com/BornToBeRoot/NETworkManager) by BornToBeRoot, a similar tool for Windows that served as the original inspiration.

> Built with [Claude Code](https://claude.ai/code) (Anthropic) and the contribution of its author.

---

## Screenshots

> Screenshots from v1.2.7 — the app now has 27 modules and 8 interface languages (FR/EN/ES/DE/IT/PT/JA/ZH).

| Dashboard | Topology |
|-----------|----------|
| ![Dashboard](screenshots/main_v1.2.7.png) | ![Topology](screenshots/topology_v1.2.7.png) |

| Traceroute | Wi-Fi |
|------------|-------|
| ![Traceroute](screenshots/traceroute_v1.2.7.png) | ![Wi-Fi](screenshots/Wi-Fi_v1.2.7.png) |

---

## Changelog

### v1.3.5 — 2026-06-06

- **macOS compatibility** — all 9 network modules now run on macOS without breaking Linux behaviour; each module detects the platform at startup (`_IS_MACOS`) and branches to native macOS commands: `route -n get default`, `ifconfig`, `scutil --dns`, `networksetup`, `system_profiler SPAirPortDataType`, `pfctl`, `netstat -ib`; privilege escalation uses `osascript` + `with administrator privileges` instead of `pkexec`; monospace font uses `Menlo` instead of `Monospace`
- **Modules with dual Linux/macOS paths**: Dashboard, Interfaces, Wi-Fi, Topology, Bandwidth, Firewall (pf.conf + pfctl), Connection Manager, Hosts File, MTR
- **Modules unchanged** (tools identical on both platforms): DNS, Nmap Scan, SNMP, Whois

### v1.3.2 — 2026-06-06

- **i18n extended to 8 languages** — added Italiano, Português, 日本語 (Japanese) and 中文 (Chinese Simplified); the full UI (all 27 modules, ~720 translation keys) is now available in FR / EN / ES / DE / IT / PT / JA / ZH; a restart prompt appears after changing the language in Settings
- **Contextual help in 8 languages** — the `?` badge panel (description, usage examples and equivalent CLI commands) now covers all 8 languages for every module; previously JA and ZH fell back to English
- **Bug fix** — nav tooltips for SMB/NFS and Hosts File were displaying in French regardless of the selected language; missing `nav_hint_smb_nfs` and `nav_hint_hosts` keys added to all 7 non-French language blocks

### v1.3.1 — 2026-06-05

- **SSH Key Manager** — list all key pairs in `~/.ssh/` (file, type, bits, comment, SHA256 fingerprint); generate Ed25519 or RSA 4096 keys with optional passphrase (mismatch detection, auto-filename by type); copy public key to clipboard; deploy to a remote server via `ssh-copy-id` in an inline terminal with stdin support for password prompts; delete key pairs with confirmation; auto-creates `~/.ssh/` if missing; i18n: fr / en / es / de

### v1.3.0 — 2026-06-03

- **TLS / SSL Inspector** — inspect any server's certificate: subject CN, SANs, issuer, validity dates (color-coded: green / orange < 30 days / red expired), serial number, TLS protocol, cipher suite and certificate chain (via `openssl s_client`); works for valid, expired and self-signed certs; friendly error messages for unreachable hosts
- **SMB / NFS Browser** — list shares and exports from any server; SMB tab: `smbclient -L` with optional credentials, shows share name / type / comment; NFS tab: `showmount -e`, shows export path and access list; detects missing tools with distro-specific install instructions
- **Hosts File Editor** — view and edit `/etc/hosts`; table with enable/disable toggle, add/edit/delete entries via dialog; filter by IP or hostname; saves via `pkexec cp` (polkit authentication dialog)
- **install.sh** — new script for Debian / Ubuntu / Linux Mint: creates a venv in `~/.local/share/nmlinux/venv`, installs system deps via apt, creates launcher and `.desktop` entry (fixes PEP 668 `externally-managed-environment` error)

### v1.2.9 — 2026-05-30

- **VNC** — new module for managing VNC connection profiles; groups/subgroups like SSH and RDP; launches `vncviewer` (TigerVNC); compatible with macOS ARD (DH30 auth handled natively by vncviewer); password never stored; detects missing `vncviewer` with distro-specific install instructions
- **About — Tools & services** — new section listing all third-party tools and APIs the app depends on
- **Sidebar i18n** — all 23 nav tooltips now translated into FR/EN/ES/DE (were hardcoded French); labels corrected: Topology, Connections, Subnet

### v1.2.8 — 2026-05-30

- **Remote Desktop (RDP)** — new module for managing Windows RDP connection profiles; groups/subgroups like SSH; launches `xfreerdp` as an external process; password prompted at connect time, never stored; fields: host, port, username, domain, resolution, fullscreen; detects missing `xfreerdp` with distro-specific install instructions (Arch / Debian / Fedora)

### v1.2.7 — 2026-05-26

- **Bundled Lucide icons** — 21 SVG icons from [Lucide](https://lucide.dev) (MIT) are now bundled in `assets/icons/`; rendered at runtime via `QSvgRenderer`; coloured `#60a5fa`; app no longer requires any system icon theme (Breeze, Adwaita, Papirus…)

### v1.2.6 — 2026-05-24

- **GNOME / Adwaita compatibility** — fixed icons on non-KDE desktops: `main.py` now auto-detects the GTK icon theme via `gsettings` and applies it to Qt; extended fallback chains for Wi-Fi, Traceroute, Speed Test, Interfaces, Port Scanner, Firewall, MTR; `themed_icon()` now validates that a real pixmap exists before accepting a theme icon
- **NixOS / KDE compatibility** — fixed all icons on NixOS: Breeze 6.x ships SVGZ-only icons; the Nix wrapper now adds `qt6.qtsvg` to `QT_PLUGIN_PATH` so Qt can render SVG icons; `themed_icon()` tries sizes 22/24/16/32/48 (Breeze uses 22 px, not 24); theme forced to `breeze` when the Nix-bundled icon set is detected; also checks `/etc/xdg/kdeglobals` for system-wide KDE config

### v1.2.5 — 2026-05-23

- **MTR** — embedded My Traceroute: runs `mtr --report`, parses text output, displays a live table with Loss %, RTT Last/Avg/Best/Worst/Jitter per hop, colour-coded by loss severity; continuous mode; CSV + TXT export
- **Speed Test** — dependency-free speed test via `curl` + Cloudflare (`speed.cloudflare.com`): download (25 MB), upload (10 MB), ping to `1.1.1.1`; up to 5 runs persisted in JSON; historical line graph (Download/Upload)
- **Firewall Viewer** — read-only ruleset viewer: parses `/etc/nftables.conf` and `/etc/iptables/*.rules` without root; live ruleset via `pkexec nft list ruleset`; columns: Table / Chain / Rule / Port / Action / Comment; colour-coded actions; live filter
- **Sidebar hints** — each nav entry now shows a subtle `?` badge; hovering displays a tooltip describing what the module does; vertical separator added between sidebar and content area
- **i18n** — all new modules translated in French, English, and Spanish

### v1.2.0 — 2026-05-22

- **Theme adaptation** — full runtime light/dark switching support across all pages; new `core/theme.py` with `is_dark()`, `color_ok()`, `color_err()`; custom painter widgets (`_Graph`, `_MapWidget`) read palette at paint time; all hardcoded Catppuccin Mocha colours replaced with semantic Qt palette roles
- **Subnet mask** — Dashboard, Interfaces, and Connexions pages now display dotted-decimal subnet mask (e.g. `255.255.255.0`) derived from CIDR prefix
- **Bandwidth Monitor** — explicit Start/Stop button replaces unreliable auto-start on page load
- **Export CSV/TXT** — Nmap and Traceroute pages now offer Export CSV and Export TXT buttons (appear after scan/trace completes)
- **i18n** — new translation keys for all above features (fr/en/es/de)

### v1.1.1 — 2026-05-16

- **SSH terminal** — complete rewrite with [pyte](https://github.com/selectel/pyte) (VT100/xterm emulator) + QPainter renderer; 2000-line scrollback, cursor blink, 256-colour support
- **Visual Traceroute** — world map (Natural Earth 110m), live geolocation per hop (ip-api.com), interactive zoom/pan, dual parser (`traceroute` / `tracepath` fallback)
- **Bandwidth Monitor** — real-time per-interface throughput, 60s sliding graph, live speeds, session totals and peaks
- **Wake on LAN** — pure Python magic packet (UDP broadcast), persistent host book (JSON)
- **IP Scanner** — hostname resolution via `getent`/`avahi`/`nmblookup`; MAC address, vendor (IEEE OUI 39K entries), interface columns; CSV/TXT export updated
- **i18n** — full fr/en/es/de translation for all new pages

### v1.0.0 — 2026-05-14

Initial public release — 13 modules: Dashboard, Interfaces, Wi-Fi, Subnet Calculator, DNS Lookup, Ping Monitor, IP Scanner, Port Scanner, Nmap, Whois, SNMP, SNTP/NTP, SSH.

---

## Features

| Module | Description |
|--------|-------------|
| **Dashboard** | Local machine info, gateway, public IP, geolocation, DNS resolvers |
| **Connection Manager** | NetworkManager profiles via `nmcli`: list, filter, connect/disconnect/edit/delete |
| **Interfaces** | Network interfaces table with per-interface detail (`ip` + `nmcli`) |
| **Wi-Fi** | Available networks, signal bars, security, connected network highlighted |
| **Subnet Calculator** | Network/broadcast/host range from CIDR, host table up to 4096 entries |
| **DNS Lookup** | `dig`-based lookup for A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY |
| **Ping Monitor** | Continuous ping to multiple hosts, RTT stats, packet loss % |
| **IP Scanner** | CIDR/range ping scan, 50 threads, hostname (DNS/mDNS/NetBIOS), MAC address, vendor (OUI), interface, CSV + TXT export |
| **Port Scanner** | TCP connect scan, 200 threads, service presets, CSV + TXT export |
| **Nmap** | 7 scan modes, XML output parsing, Host/Port/Protocol/State/Service table, CSV + TXT export |
| **Whois** | Raw whois output in monospace |
| **SNMP** | `snmpwalk`/`snmpget`, v1/v2c, 10 OID presets, results table |
| **SNTP / NTP** | Pure Python RFC 4330 UDP client, offset/delay/stratum/reference |
| **SSH** | Embedded PTY terminal (pyte/VT100), saved connections (JSON), key auth, scrollback |
| **Remote Desktop** | RDP connection profiles (groups/subgroups); launches `xfreerdp`; password never stored |
| **VNC** | VNC connection profiles (groups/subgroups); launches `vncviewer` (TigerVNC); macOS ARD compatible; password never stored |
| **TLS Inspector** | Certificate details: CN, SANs, issuer, validity + expiry countdown, serial, protocol, cipher, chain |
| **SMB / NFS** | List SMB shares (`smbclient`) and NFS exports (`showmount`) from any server or NAS; optional credentials for SMB |
| **Hosts File** | View/edit `/etc/hosts`: add, delete, toggle entries; filter; save via pkexec |
| **Visual Traceroute** | Hop-by-hop route on a world map, live geolocation (ip-api.com), zoom & pan, CSV + TXT export |
| **MTR** | Embedded My Traceroute: loss %, RTT Last/Avg/Best/Worst/Jitter per hop, colour-coded, CSV + TXT export |
| **Firewall Viewer** | Read-only nftables + iptables/ip6tables ruleset (no root); live via pkexec; filter by table/chain/action |
| **Speed Test** | Download/upload/ping via Cloudflare; no external tool beyond `curl`; history graph (last 5 runs) |
| **Bandwidth** | Real-time per-interface throughput: 60s sliding graph, live speeds, session totals, peak |
| **Wake on LAN** | Pure Python magic packet (UDP broadcast), persistent host book, no external tool required |
| **Topology Map** | Auto-discovers LAN devices via `nmap -sn`; interactive graph with draggable nodes, zoom/pan, detail panel |
| **Settings** | Language selection (FR / EN / ES / DE / IT / PT / JA / ZH), persisted; restart required after change |

---

## Requirements

### System tools

Most are already present on a standard Linux install:

```bash
# Arch / EndeavourOS
sudo pacman -S iproute2 networkmanager bind-tools nmap whois net-snmp iputils mtr curl

# Debian / Ubuntu
sudo apt install iproute2 network-manager dnsutils nmap whois snmp mtr-tiny curl

# Fedora
sudo dnf install iproute NetworkManager bind-utils nmap whois net-snmp-utils mtr curl
```

### Optional tools

| Tool | Feature | Package |
|------|---------|---------|
| `xfreerdp` / `xfreerdp3` | Remote Desktop (RDP) | Arch: `freerdp` · Debian: `freerdp2-x11` · Fedora: `freerdp` |
| `vncviewer` | VNC | Arch: `tigervnc` · Debian: `tigervnc-viewer` · Fedora: `tigervnc` |
| `nm-connection-editor` | Edit connections from Connection Manager | Arch: `nm-connection-editor` |
| `traceroute` | Traceroute alternative (tracepath used by default) | Arch: `traceroute` |

### Python

- Python 3.11+
- PySide6 6.6+
- ptyprocess 0.7+
- pyte 0.8+ (`pip install pyte` or `sudo pacman -S python-pyte`)

---

## Installation

### Option 1 — Arch Linux / Manjaro / EndeavourOS (AUR)

```bash
yay -S nmlinux
```

All dependencies (PySide6, ptyprocess, pyte, nmcli, …) are handled automatically.

### Option 2 — Debian / Ubuntu / Linux Mint (install script)

> **Note for Linux Mint / Ubuntu users:** `pip install` is blocked system-wide on Python 3.12+ (PEP 668 — `externally-managed-environment`). Use the provided install script — it creates a virtual environment automatically and installs a `.desktop` entry.

```bash
git clone https://github.com/thongor77/nmlinux.git
cd nmlinux
bash install.sh
```

The script will:
- Install system dependencies via `apt` (libgl1, python3-venv, freerdp, tigervnc…)
- Create a virtual environment in `~/.local/share/nmlinux/venv`
- Install NMLinux and its Python dependencies inside the venv
- Create a launcher at `~/.local/bin/nmlinux`
- Add a `.desktop` entry so NMLinux appears in your application menu

After install, run `nmlinux` from a terminal or launch it from the application menu.

### Option 3 — Wheel (all distros)

Download the `.whl` from the [latest release](https://github.com/thongor77/nmlinux/releases/latest) and install it:

```bash
# Arch / Fedora / distros without pip restrictions
pip install nmlinux-1.2.9-py3-none-any.whl

# Debian / Ubuntu / Mint — use pipx or a venv instead
pipx install nmlinux-1.2.9-py3-none-any.whl
```

### Option 4 — From source (Arch / Fedora)

```bash
git clone https://github.com/thongor77/nmlinux.git
cd nmlinux
pip install PySide6 ptyprocess pyte
python3 -m nmlinux.main
```

### Option 5 — Desktop entry (KDE / GNOME / etc.)

Copy the `.desktop` file to make NMLinux appear in your application launcher:

```bash
cp data/nmlinux.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

Then edit the `Exec=` path in the file if needed.

---

## Running

```bash
./nmlinux.sh
# or, after pip install:
nmlinux
# or directly:
python3 -m nmlinux.main
```

---

## Project structure

```
nmlinux/
  core/
    i18n.py         — Translation system (8 languages: fr/en/es/de/it/pt/ja/zh), tr(key) function
    icons.py        — themed_icon(): 21 bundled Lucide SVG icons via QSvgRenderer
    settings.py     — AppSettings dataclass, JSON persistence
    ssh.py          — SshConnection dataclass, SshStore
    rdp.py          — RdpConnection dataclass, RdpStore, find_xfreerdp()
    vnc.py          — VncConnection dataclass, VncStore, find_vncviewer()
    terminal.py     — SshWorker (QThread) + PTY via ptyprocess, emits raw bytes
    cli_bar.py      — CliBar singleton: pedagogical CLI equivalent bar
  pages/
    about.py        — About page (credits, tools & services)
    bandwidth.py    — Bandwidth Monitor: per-interface 60s graph, live stats
    connection_manager.py — Connection Manager: nmcli profiles, connect/disconnect/edit
    dashboard.py    — Dashboard
    dns.py          — DNS Lookup
    firewall.py     — Firewall Viewer: nftables + iptables parser, live via pkexec
    interfaces.py   — Network Interfaces
    ip_scanner.py   — IP Scanner
    mtr.py          — MTR: mtr --report parser, live hop stats table, export
    nmap_scan.py    — Nmap
    ping.py         — Ping Monitor
    port_scanner.py — Port Scanner
    rdp.py          — Remote Desktop: RDP profiles, launches xfreerdp
    settings.py     — Settings page
    snmp.py         — SNMP
    sntp.py         — SNTP / NTP
    speedtest.py    — Speed Test: curl + Cloudflare, history graph
    ssh.py          — SSH page (connection manager + terminal)
    subnet.py       — Subnet Calculator
    terminal_view.py — TerminalView: pyte VT100 emulator + QPainter renderer
    topology.py     — Topology Map: nmap -sn, interactive graph, zoom/pan
    traceroute.py   — Visual Traceroute: world map, geolocation, zoom/pan
    vnc.py          — VNC: connection profiles, launches vncviewer
    whois.py        — Whois
    wifi.py         — Wi-Fi
    wol.py          — Wake on LAN: magic packet, persistent host book
  assets/
    icons/          — 21 bundled Lucide SVG icons (#60a5fa)
    world.geojson   — Natural Earth 110m countries (map background)
  window.py         — MainWindow (sidebar + QStackedWidget)
  main.py           — Entry point
```

---

## Desktop environment compatibility

Since v1.2.7, NMLinux uses 21 bundled [Lucide](https://lucide.dev) SVG icons rendered at runtime via `QSvgRenderer`. The app no longer depends on any system icon theme (Breeze, Adwaita, Papirus…) and displays correctly on KDE, GNOME, XFCE, and others. The Qt style adapts to the running desktop automatically.

---

## Limitations

- Linux only (relies on `nmcli`, `ip`, `dig`, `ping`, subprocess tools)
- No root/polkit integration — tools requiring elevated privileges (some Nmap
  modes, raw sockets) must be run manually with `sudo`
- SSH supports password and key-based auth; agent forwarding not yet implemented

---

## Credits and acknowledgements

- **[BornToBeRoot](https://github.com/BornToBeRoot)** — for [NETworkManager](https://github.com/BornToBeRoot/NETworkManager), the original inspiration and reference for features and UX
- **[Anthropic](https://www.anthropic.com)** — Claude Code, the AI assistant used to build this project
- The author, for the vision, testing, and direction

---

## License

GPL-2.0 — see [LICENSE](LICENSE).

This project is an independent reimplementation. No code from NETworkManager was used or translated.
