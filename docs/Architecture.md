# Architecture de NMLinux

## Vue d'ensemble

NMLinux est une application de bureau Linux mono-processus, mono-fenêtre, construite avec Python 3.11+ et PySide6 (Qt 6). Elle regroupe 29 outils réseau dans une interface à sidebar unique.

```
nmlinux/
├── main.py            — point d'entrée, QApplication, détection thème icônes
├── window.py          — MainWindow, sidebar QListWidget, QStackedWidget
├── core/              — logique partagée, sans dépendance Qt sauf cli_bar, icons, host_actions
│   ├── i18n.py        — tr(key, **kwargs) : 8 langues, ~720 clés chacune
│   ├── settings.py    — AppSettings dataclass, persistence JSON singleton
│   ├── theme.py       — is_dark(), color_ok(), color_err()
│   ├── icons.py       — themed_icon(*names) : Lucide SVG bundlés
│   ├── cli_bar.py     — CliBar singleton : barre CLI pédagogique globale
│   ├── help_content.py— get_help(label) : aide contextuelle 8 langues × 28 modules (File Transfer non couvert)
│   ├── host_actions.py— HostActionMenu : menu contextuel générique pour les liens inter-modules (v1.7.0)
│   ├── asset_collectors.py — AssetScanWorker + _collect_ssh/_collect_winrm/_collect_snmp (Asset Inventory)
│   ├── smb_mount.py   — mount()/unmount() SMB/NFS via pkexec (Linux + macOS)
│   ├── export_dialog.py — ExportDialog générique (JSON/MD/TXT/PDF) réutilisé par plusieurs pages
│   ├── ssh.py         — SshGroup, SshConnection, SshStore, build_ssh_args()
│   ├── rdp.py         — RdpGroup, RdpConnection, RdpStore, build_rdp_args()
│   ├── vnc.py         — VncGroup, VncConnection, VncStore, build_vnc_args()
│   └── terminal.py    — SshWorker(QThread) : PTY via ptyprocess, émet bytes bruts
├── pages/             — un QWidget par module
│   ├── terminal_view.py — TerminalView : pyte.HistoryScreen + QPainter
│   └── [29 pages]
└── assets/
    ├── icons/         — 21 SVG Lucide (couleur #60a5fa appliquée au runtime)
    └── world.geojson  — Natural Earth 110m pour la carte Traceroute
```

## MainWindow et enregistrement des pages

`window.py` déclare `_TOOLS` : liste de tuples `(icon_names, label, PageClass, tooltip)`. Chaque entrée génère automatiquement un item dans la sidebar et une page dans le `QStackedWidget`.

Ordre des 29 modules dans `_TOOLS` :

| # | Label | Classe |
|---|-------|--------|
| 1 | Dashboard | DashboardPage |
| 2 | Connections | ConnectionManagerPage |
| 3 | Interfaces | InterfacesPage |
| 4 | Wi-Fi | WifiPage |
| 5 | Subnet | SubnetPage |
| 6 | DNS | DnsPage |
| 7 | Ping | PingPage |
| 8 | IP Scanner | IpScannerPage |
| 9 | Port Scanner | PortScannerPage |
| 10 | Nmap | NmapPage |
| 11 | Whois | WhoisPage |
| 12 | TLS Inspector | TlsPage |
| 13 | SMB / NFS | SmbNfsPage |
| 14 | Hosts File | HostsPage |
| 15 | SNMP | SnmpPage |
| 16 | SNTP / NTP | SntpPage |
| 17 | SSH | SshPage |
| 18 | SSH Keys | SshKeysPage |
| 19 | Remote Desktop | RdpPage |
| 20 | VNC | VncPage |
| 21 | Traceroute | TraceroutePage |
| 22 | MTR | MtrPage |
| 23 | Firewall | FirewallPage |
| 24 | Speed Test | SpeedTestPage |
| 25 | Bandwidth | BandwidthPage |
| 26 | Wake on LAN | WolPage |
| 27 | File Transfer | FileTransferPage |
| 28 | Topology | TopologyPage |
| 29 | Asset Inventory | AssetInventoryPage |

Settings et About sont hors `_TOOLS`, ajoutés manuellement dans `MainWindow._build_ui()` aux indices `len(_TOOLS)` et `len(_TOOLS) + 1`.

La sidebar affiche également un badge `?` par entrée (via `_NavHintDelegate`). Un clic sur `?` remplace la page active par `HelpPage` (index `len(_TOOLS) + 2`).

## Liens inter-modules (v1.7.0)

`core/host_actions.py` fournit `HostActionMenu(QMenu)`, un menu contextuel générique instancié par toute page affichant une table d'IP/hostnames (IP Scanner, Nmap, Topology, Asset Inventory, …). Il émet `action_chosen = Signal(action_key, ip, host)` avec `action_key` parmi les constantes `ACT_*` (`ping`, `port_scan`, `whois`, `dns`, `traceroute`, `mtr`, `ssh`, `rdp`, `vnc`, `topology`, `asset`, `smb`). Les entrées SSH/RDP/VNC/SMB apparaissent en gras quand le port correspondant (22/3389/5900/445) est détecté ouvert.

`MainWindow` connecte ce signal à un routeur central qui appelle `set_target(ip)` sur la page cible (pattern déjà posé par TLS Watchlist → sidebar) puis `navigate_to(idx)`. Couplage nul entre les pages elles-mêmes — toute la logique de routage vit dans `window.py`.

## Pattern standard d'une page

```python
class FooPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: FooWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        # Constantes de colonnes au niveau module : _C_IP, _C_HOST, ... = range(N)
        # layout.addWidget(table, 10) + layout.addStretch(1) pour éviter le centrage Qt

    def showEvent(self, event) -> None:
        self._update_cli()
        super().showEvent(event)

    def _update_cli(self) -> None:
        if bar := get_cli_bar():
            bar.set_cmd("cmd ...")
```

## Pattern Worker (QThread)

Tout travail réseau ou système bloquant s'exécute dans un `QThread` dédié :

```python
class FooWorker(QThread):
    result = Signal(dict)   # données partielles ou complètes
    error  = Signal(str)

    def run(self) -> None:
        # ... travail bloquant ...
        self.result.emit(data)

    def stop(self) -> None:
        self._stop_flag = True
        self.wait(2000)
```

La page crée le worker dans `_build_ui`, connecte les signaux, appelle `worker.start()` sur action utilisateur et `worker.stop()` dans `hideEvent` / `closeEvent`.

## Terminal PTY (SSH, SSH Keys)

- `core/terminal.py` — `SshWorker(QThread)` : spawn via `ptyprocess.PtyProcess`, lit 4096 octets par cycle, émet `output(bytes)` bruts.
- `pages/terminal_view.py` — `TerminalView(QWidget)` : feed les bytes dans `pyte.HistoryScreen(2000)`, redessine case par case avec `QPainter` à chaque `update()`. Palette Catppuccin Mocha fixe. Scrollback via `QScrollBar` intégré.

## Icônes

`core/icons.py` : `themed_icon(*names)` cherche le premier nom reconnu dans `_NAME_MAP` → nom SVG Lucide. `_load_icon()` (avec `@lru_cache`) remplace `stroke="currentColor"` par `#60a5fa` et rend à 22 px via `QSvgRenderer + QPainter`. L'application ne dépend d'aucun thème système.

## Thème clair/sombre

`core/theme.py` : `is_dark()` lit `QPalette.Window.lightness() < 128`. Les widgets avec dessin custom (`QPainter`) doivent : (1) appeler `color_ok()` / `color_err()` à la création des widgets — jamais au chargement du module — et (2) surcharger `changeEvent(ApplicationPaletteChange)` + appeler `update()`.

## Internationalisation

`core/i18n.py` : `_T: dict[str, dict[str, str]]` — code langue → clé → chaîne. `tr(key, **kwargs)` cherche dans la langue courante, tombe back sur `fr`. La langue est dans `AppSettings.language` (singleton chargé à l'import). Langues : `fr`, `en`, `es`, `de`, `it`, `pt`, `ja`, `zh`.

L'aide contextuelle est dans `core/help_content.py` : `_CONTENT: dict[str, dict[str, dict]]` — label module → code langue → `{desc, examples, cli}`. `get_help(label)` retourne le contenu dans la langue courante avec fallback `en` → `fr`.

## Persistence

Toutes les données utilisateur sont dans `~/.local/share/nmlinux/` :

| Fichier | Contenu |
|---------|---------|
| `settings.json` | `AppSettings` (langue) |
| `ssh_connections.json` | Groupes + connexions SSH v2 |
| `rdp_connections.json` | Groupes + connexions RDP v2 |
| `vnc_connections.json` | Groupes + connexions VNC v2 |
| `wol_hosts.json` | Hôtes Wake on LAN |
| `speedtest_history.json` | Historique 5 derniers tests de débit |
| `ping_targets.json` | Répertoire de cibles Ping Monitor (`PingTarget`, v1.7.5) |

Un fichier échappe à ce répertoire pour des raisons historiques : `~/.config/nmlinux/tls_watchlist.json` (certificats surveillés par TLS Watchlist, `core/tls_watchlist.py`).

Format JSON v2 pour SSH/RDP/VNC : `{version: 2, groups: [...], connections: [...]}`. Rétrocompatibilité v1 (liste plate) dans `SshStore.load()`.

## Dépendances Python

| Package | Rôle |
|---------|------|
| `PySide6 >= 6.6` | Framework Qt (inclut QtSvg) |
| `ptyprocess >= 0.7` | PTY pour le terminal SSH |
| `pyte` | Émulateur VT100/xterm pour le terminal |
| `tftpy >= 0.8` | Serveur TFTP pour File Transfer |

Optionnel, non déclaré dans `pyproject.toml` (import protégé par `try/except`) : `pywinrm` — collecte WinRM dans Asset Inventory (`pip install pywinrm`).

## Dépendances système

Obligatoires : `networkmanager` (nmcli), `iproute2` (ip), `iputils` (ping, tracepath)

Optionnelles : `nmap`, `whois`, `net-snmp`, `bind` (dig), `traceroute`, `python-hwdata`, `nm-connection-editor`, `samba` (smbclient), `cifs-utils` (mount.cifs, montage SMB), `nfs-utils` (showmount), `openssl`, `xfreerdp` / `xfreerdp3`, `vncviewer` (TigerVNC), `mtr`, `curl`, `wakeonlan`, `ssh-keygen` (openssh), `pkexec` (polkit), `sshpass` (auth SSH par mot de passe dans Asset Inventory)

## Lancement

```bash
# Développement
python3 -m nmlinux.main
# ou
./nmlinux.sh

# Installé
nmlinux
```
