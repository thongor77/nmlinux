# Inter-Module Links + Dashboard Mini-Widgets — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un menu contextuel (clic droit) universel sur toutes les tables de résultats contenant des IPs/hostnames, permettant de naviguer directement vers n'importe quel module pertinent, plus deux mini-widgets passifs dans le Dashboard (ping gateway + résumé TLS).

**Architecture:** Un `HostActionMenu(QMenu)` centralisé dans `core/host_actions.py` émet `action_chosen(action_key, ip, host)`. Chaque page source le relaie via son propre `action_requested` signal. `MainWindow._on_host_action` route vers la page cible et appelle `set_target()` / `load_hosts()` / `prefill_hosts()`. Aucune page source ne connaît les pages cibles.

**Tech Stack:** PySide6 (QMenu, QThread, QPainter, Signal), Python 3.11+, pytest

## Global Constraints

- Python ≥ 3.11, PySide6, pas de nouvelles dépendances externes
- Labels du menu via `tr()` (clés i18n à ajouter plus tard — pour cette version, strings en dur en français/anglais)
- `set_target` ne lance jamais de réseau si l'action est longue ou destructive (Port Scanner, DNS, SSH/RDP/VNC)
- `set_target` lance automatiquement si rapide et non-destructif (Ping, Whois, Traceroute, MTR)
- Commits fréquents, un par tâche minimum

---

## Fichiers créés ou modifiés

| Fichier | Nature |
|---------|--------|
| `nmlinux/core/host_actions.py` | **Nouveau** — HostActionMenu + ACT_* constants |
| `tests/test_host_actions.py` | **Nouveau** — tests unitaires HostActionMenu |
| `nmlinux/window.py` | Modifié — `_page_index`, `_setup_host_action_routes`, `_on_host_action`, wiring TLS→Dashboard |
| `nmlinux/pages/whois.py` | Modifié — cible `set_target` |
| `nmlinux/pages/dns.py` | Modifié — cible `set_target` |
| `nmlinux/pages/ping.py` | Modifié — source + cible `set_target` |
| `nmlinux/pages/traceroute.py` | Modifié — source + cible `set_target` |
| `nmlinux/pages/mtr.py` | Modifié — source + cible `set_target` |
| `nmlinux/pages/port_scanner.py` | Modifié — source (ports connus) + cible `set_target` |
| `nmlinux/pages/ip_scanner.py` | Modifié — source + `_last_scan_hosts` |
| `nmlinux/pages/nmap_scan.py` | Modifié — source + `_last_scan_hosts` agrégé par hôte |
| `nmlinux/pages/ssh.py` | Modifié — cible `set_target` |
| `nmlinux/pages/rdp.py` | Modifié — cible `set_target` |
| `nmlinux/pages/vnc.py` | Modifié — cible `set_target` |
| `nmlinux/pages/topology.py` | Modifié — `_NodeItem` signal interne + `TopologyPage` source + cible `load_hosts` |
| `nmlinux/core/asset_collectors.py` | Modifié — `AssetScanWorker` accepte liste de hosts optionnelle |
| `nmlinux/pages/asset_inventory.py` | Modifié — cible `prefill_hosts` |
| `nmlinux/pages/dashboard.py` | Modifié — `_GatewayPingWorker`, `_MiniPingGraph`, `set_tls_summary` |

---

## Task 1 — `core/host_actions.py` + tests

**Files:**
- Create: `nmlinux/core/host_actions.py`
- Create: `tests/test_host_actions.py`

**Interfaces:**
- Produces:
  - `ACT_PING`, `ACT_PORT_SCAN`, `ACT_WHOIS`, `ACT_DNS`, `ACT_TRACEROUTE`, `ACT_MTR`, `ACT_SSH`, `ACT_RDP`, `ACT_VNC`, `ACT_TOPOLOGY`, `ACT_ASSET` — string constants
  - `HostActionMenu(ip, host='', ports=None, parent=None)` — `QMenu` subclass
  - `HostActionMenu.action_chosen` — `Signal(str, str, str)` (action_key, ip, host)

- [ ] **Step 1: Écrire le test**

```python
# tests/test_host_actions.py
from __future__ import annotations
import sys
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    return app

from nmlinux.core.host_actions import (
    HostActionMenu,
    ACT_PING, ACT_PORT_SCAN, ACT_WHOIS, ACT_DNS,
    ACT_TRACEROUTE, ACT_MTR, ACT_SSH, ACT_RDP,
    ACT_VNC, ACT_TOPOLOGY, ACT_ASSET,
)

def test_all_actions_present(qapp):
    menu = HostActionMenu("1.2.3.4")
    keys = set()
    menu.action_chosen.connect(lambda k, ip, h: keys.add(k))
    for action in menu.actions():
        if not action.isSeparator():
            action.trigger()
    assert keys == {ACT_PING, ACT_PORT_SCAN, ACT_WHOIS, ACT_DNS,
                    ACT_TRACEROUTE, ACT_MTR, ACT_SSH, ACT_RDP,
                    ACT_VNC, ACT_TOPOLOGY, ACT_ASSET}

def test_signal_carries_ip_and_host(qapp):
    received = []
    menu = HostActionMenu("10.0.0.1", "myhost")
    menu.action_chosen.connect(lambda k, ip, h: received.append((ip, h)))
    for action in menu.actions():
        if ACT_PING in action.text().lower() or "ping" in action.text().lower():
            action.trigger()
            break
    assert received and received[0] == ("10.0.0.1", "myhost")

def test_bold_when_port_detected(qapp):
    menu = HostActionMenu("1.2.3.4", ports=[22, 3389])
    bold_labels = {a.text() for a in menu.actions() if not a.isSeparator() and a.font().bold()}
    assert "SSH" in bold_labels
    assert "RDP" in bold_labels
    assert "VNC" not in bold_labels

def test_no_bold_without_ports(qapp):
    menu = HostActionMenu("1.2.3.4")
    bold_labels = {a.text() for a in menu.actions() if not a.isSeparator() and a.font().bold()}
    assert not bold_labels
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
cd /home/luust/claude-projects/nmlinux && python -m pytest tests/test_host_actions.py -v
```
Attendu : `ModuleNotFoundError: No module named 'nmlinux.core.host_actions'`

- [ ] **Step 3: Créer `nmlinux/core/host_actions.py`**

```python
from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenu

ACT_PING       = "ping"
ACT_PORT_SCAN  = "port_scan"
ACT_WHOIS      = "whois"
ACT_DNS        = "dns"
ACT_TRACEROUTE = "traceroute"
ACT_MTR        = "mtr"
ACT_SSH        = "ssh"
ACT_RDP        = "rdp"
ACT_VNC        = "vnc"
ACT_TOPOLOGY   = "topology"
ACT_ASSET      = "asset"

_PORT_SSH = 22
_PORT_RDP = 3389
_PORT_VNC = 5900


class HostActionMenu(QMenu):
    action_chosen = Signal(str, str, str)  # action_key, ip, host

    def __init__(
        self,
        ip: str,
        host: str = '',
        ports: list[int] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ip    = ip
        self._host  = host
        self._ports = set(ports) if ports else set()

        title = host if (host and host != ip) else ip
        self.setTitle(title)

        self.addSection("Naviguer vers")
        self._add(ACT_PING,       "Ping")
        self._add(ACT_PORT_SCAN,  "Scanner les ports")
        self._add(ACT_WHOIS,      "Whois")
        self._add(ACT_DNS,        "DNS")
        self._add(ACT_TRACEROUTE, "Traceroute")
        self._add(ACT_MTR,        "MTR")

        self.addSection("Connexion")
        self._add(ACT_SSH, "SSH", bold=_PORT_SSH in self._ports)
        self._add(ACT_RDP, "RDP", bold=_PORT_RDP in self._ports)
        self._add(ACT_VNC, "VNC", bold=_PORT_VNC in self._ports)

        self.addSection("Inventaire")
        self._add(ACT_TOPOLOGY, "Voir en Topologie")
        self._add(ACT_ASSET,    "Ajouter à l'inventaire")

    def _add(self, key: str, label: str, bold: bool = False) -> None:
        action = self.addAction(label)
        if bold:
            f = action.font()
            f.setBold(True)
            action.setFont(f)
        action.triggered.connect(
            lambda _checked=False, k=key: self.action_chosen.emit(k, self._ip, self._host)
        )
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
python -m pytest tests/test_host_actions.py -v
```
Attendu : 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add nmlinux/core/host_actions.py tests/test_host_actions.py
git commit -m "feat: add HostActionMenu with ACT_* constants and tests"
```

---

## Task 2 — MainWindow infrastructure

**Files:**
- Modify: `nmlinux/window.py`

**Interfaces:**
- Consumes: `ACT_*` constants et `HostActionMenu` de `core/host_actions`
- Produces:
  - `MainWindow._page_index(class_name: str) -> int`
  - `MainWindow._setup_host_action_routes() -> None`
  - `MainWindow._on_host_action(action: str, ip: str, host: str) -> None`
  - Auto-connexion de `action_requested` pour toutes les pages sources

- [ ] **Step 1: Ajouter l'import dans `window.py`**

En haut de `window.py`, après les imports existants :
```python
from nmlinux.core.host_actions import (
    ACT_PING, ACT_PORT_SCAN, ACT_WHOIS, ACT_DNS,
    ACT_TRACEROUTE, ACT_MTR, ACT_SSH, ACT_RDP,
    ACT_VNC, ACT_TOPOLOGY, ACT_ASSET,
)
```

- [ ] **Step 2: Ajouter `_page_index` à `MainWindow`**

Ajouter cette méthode dans la classe `MainWindow` (après `navigate_to`) :

```python
def _page_index(self, class_name: str) -> int:
    for i, page in enumerate(self._pages):
        if type(page).__name__ == class_name:
            return i
    raise ValueError(f"Page class not found: {class_name}")
```

- [ ] **Step 3: Ajouter `_setup_host_action_routes` dans `MainWindow`**

```python
def _setup_host_action_routes(self) -> None:
    self._host_routes: dict[str, tuple[int, object]] = {
        ACT_PING:       (self._page_index('PingPage'),
                         lambda p, ip, h, _s: p.set_target(h or ip)),
        ACT_PORT_SCAN:  (self._page_index('PortScannerPage'),
                         lambda p, ip, h, _s: p.set_target(ip)),
        ACT_WHOIS:      (self._page_index('WhoisPage'),
                         lambda p, ip, h, _s: p.set_target(h or ip)),
        ACT_DNS:        (self._page_index('DnsPage'),
                         lambda p, ip, h, _s: p.set_target(h or ip)),
        ACT_TRACEROUTE: (self._page_index('TraceroutePage'),
                         lambda p, ip, h, _s: p.set_target(h or ip)),
        ACT_MTR:        (self._page_index('MtrPage'),
                         lambda p, ip, h, _s: p.set_target(h or ip)),
        ACT_SSH:        (self._page_index('SshPage'),
                         lambda p, ip, h, _s: p.set_target(ip, h)),
        ACT_RDP:        (self._page_index('RdpPage'),
                         lambda p, ip, h, _s: p.set_target(ip, h)),
        ACT_VNC:        (self._page_index('VncPage'),
                         lambda p, ip, h, _s: p.set_target(ip, h)),
        ACT_TOPOLOGY:   (self._page_index('TopologyPage'),
                         lambda p, ip, h, src: p.load_hosts(
                             getattr(src, '_last_scan_hosts', []))),
        ACT_ASSET:      (self._page_index('AssetInventoryPage'),
                         lambda p, ip, h, src: p.prefill_hosts(
                             getattr(src, '_last_scan_hosts', []))),
    }
```

- [ ] **Step 4: Ajouter `_on_host_action` dans `MainWindow`**

```python
def _on_host_action(self, action: str, ip: str, host: str) -> None:
    if action not in self._host_routes:
        return
    idx, fn = self._host_routes[action]
    sender = self.sender()
    fn(self._pages[idx], ip, host, sender)
    self.navigate_to(idx)
```

- [ ] **Step 5: Modifier `_build_stack` pour câbler les connexions**

Dans `_build_stack`, **après** la boucle `for _, _, PageClass, _ in _TOOLS:`, ajouter :

```python
# Auto-connect source pages
for page in self._pages:
    if hasattr(page, 'action_requested'):
        page.action_requested.connect(self._on_host_action)

# Build routing table (requires all pages to be instantiated)
self._setup_host_action_routes()
```

- [ ] **Step 6: Vérifier que l'application démarre sans erreur**

```bash
python -m nmlinux.main
```
Attendu : fenêtre s'ouvre normalement. Aucun crash au démarrage (même si aucune page n'a encore `action_requested`).

- [ ] **Step 7: Commit**

```bash
git add nmlinux/window.py
git commit -m "feat: add MainWindow host action router and page index helper"
```

---

## Task 3 — Cibles simples : Whois et DNS

Ces deux pages reçoivent un host mais ne lancent pas automatiquement pour DNS.

**Files:**
- Modify: `nmlinux/pages/whois.py`
- Modify: `nmlinux/pages/dns.py`

**Interfaces:**
- Consumes: rien (pages autonomes)
- Produces:
  - `WhoisPage.set_target(target: str) -> None` — prefill + lance immédiatement
  - `DnsPage.set_target(host: str) -> None` — prefill uniquement

- [ ] **Step 1: Ajouter `set_target` dans `WhoisPage`**

Dans `nmlinux/pages/whois.py`, ajouter cette méthode dans la classe `WhoisPage` (après `_build_ui`) :

```python
def set_target(self, target: str) -> None:
    self._input.setText(target)
    self._lookup()
```

- [ ] **Step 2: Ajouter `set_target` dans `DnsPage`**

Dans `nmlinux/pages/dns.py`, ajouter dans la classe `DnsPage` :

```python
def set_target(self, host: str) -> None:
    self._input.setText(host)
```

- [ ] **Step 3: Test manuel**

Démarrer l'app : `python -m nmlinux.main`
- Aller sur Whois → laisser vide.
- Ouvrir la console Python ou mettre un breakpoint : confirmer que `set_target("google.com")` remplirait le champ et lancerait la recherche.
- *(Les pages ne sont pas encore sources — le test complet se fera après Task 7.)*

- [ ] **Step 4: Commit**

```bash
git add nmlinux/pages/whois.py nmlinux/pages/dns.py
git commit -m "feat: add set_target to WhoisPage and DnsPage"
```

---

## Task 4 — Ping : source + cible

**Files:**
- Modify: `nmlinux/pages/ping.py`

**Interfaces:**
- Consumes: `HostActionMenu`, `ACT_*` de `core/host_actions`
- Produces:
  - `PingPage.action_requested = Signal(str, str, str)`
  - `PingPage.set_target(host: str) -> None` — ajoute le host à la table + lance le ping

Rappel structure : `_C_DOT=0, _C_HOST=1, _C_SENT=2, _C_LOSS=3, _C_LAST=4, _C_MIN=5, _C_AVG=6, _C_MAX=7, _C_DEL=8`

- [ ] **Step 1: Ajouter les imports dans `ping.py`**

```python
from PySide6.QtCore import Qt, QThread, Signal
# Ajouter :
from nmlinux.core.host_actions import HostActionMenu
```

- [ ] **Step 2: Ajouter `action_requested` et `set_target` dans `PingPage`**

Dans la classe `PingPage`, après `__init__` :

```python
action_requested = Signal(str, str, str)  # action_key, ip, host

def set_target(self, host: str) -> None:
    self._input.setText(host)
    self._on_add()
```

- [ ] **Step 3: Ajouter le right-click sur la table ping**

Dans `PingPage._build_ui`, après `layout.addWidget(self._table, 1)` :

```python
self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

Ajouter la méthode :

```python
def _on_right_click(self, pos) -> None:
    row = self._table.rowAt(pos.y())
    if row < 0:
        return
    item = self._table.item(row, _C_HOST)
    if not item:
        return
    host = item.text()
    menu = HostActionMenu(host, host, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

- [ ] **Step 4: Test manuel**

```bash
python -m nmlinux.main
```
- Aller sur Ping → ajouter "8.8.8.8"
- Clic droit sur la ligne → menu contextuel avec 3 sections s'affiche
- Cliquer "Traceroute" → naviguer vers Traceroute avec "8.8.8.8" prefillé et lancé

- [ ] **Step 5: Commit**

```bash
git add nmlinux/pages/ping.py
git commit -m "feat: add Ping as source and target for inter-module navigation"
```

---

## Task 5 — Traceroute + MTR : source + cible

**Files:**
- Modify: `nmlinux/pages/traceroute.py`
- Modify: `nmlinux/pages/mtr.py`

**Interfaces:**
- Consumes: `HostActionMenu`, `ACT_*`
- Produces:
  - `TraceroutePage.action_requested = Signal(str, str, str)`
  - `TraceroutePage.set_target(host: str) -> None`
  - `MtrPage.action_requested = Signal(str, str, str)`
  - `MtrPage.set_target(host: str) -> None`

Traceroute table : colonnes 0=hop, **1=IP**, **2=hostname**, 3=rtt, 4=loc
MTR table : colonnes 0=hop, **1=host** (IP ou hostname combiné), 2=loss...

- [ ] **Step 1: Modifier `traceroute.py`**

Ajouter l'import :
```python
from nmlinux.core.host_actions import HostActionMenu
```

Dans `TraceroutePage`, ajouter signal + méthodes :

```python
action_requested = Signal(str, str, str)

def set_target(self, host: str) -> None:
    self._input.setText(host)
    self._on_start()

def _on_right_click(self, pos) -> None:
    row = self._table.rowAt(pos.y())
    if row < 0:
        return
    ip_item   = self._table.item(row, 1)
    host_item = self._table.item(row, 2)
    if not ip_item:
        return
    ip   = ip_item.text()
    host = host_item.text() if host_item else ''
    if ip in ('*', '—', ''):
        return
    menu = HostActionMenu(ip, host, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

Dans `_build_ui`, après `splitter.addWidget(self._table)` :
```python
self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

- [ ] **Step 2: Modifier `mtr.py`**

Ajouter l'import :
```python
from nmlinux.core.host_actions import HostActionMenu
```

Dans `MtrPage`, ajouter signal + méthodes :

```python
action_requested = Signal(str, str, str)

def set_target(self, host: str) -> None:
    self._input.setText(host)
    self._on_start()

def _on_right_click(self, pos) -> None:
    row = self._table.rowAt(pos.y())
    if row < 0:
        return
    host_item = self._table.item(row, 1)
    if not host_item:
        return
    host = host_item.text()
    if host in ('*', '???', ''):
        return
    menu = HostActionMenu(host, host, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

Dans `_build_ui`, après `layout.addWidget(self._table, 1)` :
```python
self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

- [ ] **Step 3: Test manuel**

```bash
python -m nmlinux.main
```
- Traceroute vers "8.8.8.8" → attendre quelques hops → clic droit sur un hop → "Ping" → navigue vers Ping avec l'IP prefillée
- MTR vers "1.1.1.1" → idem

- [ ] **Step 4: Commit**

```bash
git add nmlinux/pages/traceroute.py nmlinux/pages/mtr.py
git commit -m "feat: add source and set_target to TraceroutePage and MtrPage"
```

---

## Task 6 — Port Scanner : source + cible

Le Port Scanner est à la fois source (ports connus) et cible (prefill host).

**Files:**
- Modify: `nmlinux/pages/port_scanner.py`

**Interfaces:**
- Consumes: `HostActionMenu`, `ACT_*`
- Produces:
  - `PortScannerPage.action_requested = Signal(str, str, str)`
  - `PortScannerPage.set_target(ip: str) -> None`

Rappel : host dans `self._host_input`, colonnes table `_C_PORT=0, _C_SERVICE=1, _C_RTT=2`

- [ ] **Step 1: Ajouter les imports**

```python
from nmlinux.core.host_actions import HostActionMenu
```

- [ ] **Step 2: Ajouter signal + cible + source dans `PortScannerPage`**

```python
action_requested = Signal(str, str, str)

def set_target(self, ip: str) -> None:
    self._host_input.setText(ip)
    self._host_input.setFocus()

def _get_open_ports(self) -> list[int]:
    ports = []
    for r in range(self._table.rowCount()):
        item = self._table.item(r, _C_PORT)
        if item:
            try:
                ports.append(int(item.text()))
            except ValueError:
                pass
    return ports

def _on_right_click(self, pos) -> None:
    ip = self._host_input.text().strip()
    if not ip:
        return
    ports = self._get_open_ports() if self._table.rowCount() > 0 else None
    menu = HostActionMenu(ip, '', ports, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

Dans `_build_ui`, après la création de `self._table` :
```python
self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

- [ ] **Step 3: Test manuel**

- Scanner les ports de "192.168.1.1" → clic droit → SSH en gras si port 22 ouvert
- Naviguer depuis Ping vers Port Scanner → champ host prefillé

- [ ] **Step 4: Commit**

```bash
git add nmlinux/pages/port_scanner.py
git commit -m "feat: add source and set_target to PortScannerPage"
```

---

## Task 7 — IP Scanner : source + `_last_scan_hosts`

**Files:**
- Modify: `nmlinux/pages/ip_scanner.py`

**Interfaces:**
- Consumes: `HostActionMenu`, `ACT_*`
- Produces:
  - `IpScannerPage.action_requested = Signal(str, str, str)`
  - `IpScannerPage._last_scan_hosts: list[dict]` — rempli après chaque scan
    - Chaque dict : `{'ip': str, 'hostname': str, 'mac': str, 'vendor': str}`

Rappel colonnes : `_C_DOT=0, _C_IP=1, _C_HOST=2, _C_MAC=3, _C_VENDOR=4, _C_IFACE=5, _C_RTT=6`

- [ ] **Step 1: Ajouter les imports**

```python
from nmlinux.core.host_actions import HostActionMenu
```

- [ ] **Step 2: Initialiser `_last_scan_hosts` dans `__init__`**

Dans `IpScannerPage.__init__`, après `self._worker`:
```python
self._last_scan_hosts: list[dict] = []
```

- [ ] **Step 3: Vider `_last_scan_hosts` au début du scan**

Dans `_on_scan`, après `self._table.setRowCount(0)` :
```python
self._last_scan_hosts = []
```

- [ ] **Step 4: Remplir `_last_scan_hosts` dans `_on_found`**

Dans `_on_found(self, ip, hostname, rtt, mac, vendor, iface)`, à la fin de la méthode (après le dernier `setItem`) :
```python
self._last_scan_hosts.append({
    'ip': ip, 'hostname': hostname, 'mac': mac, 'vendor': vendor,
})
```

- [ ] **Step 5: Ajouter signal + right-click**

```python
action_requested = Signal(str, str, str)

def _on_right_click(self, pos) -> None:
    row = self._table.rowAt(pos.y())
    if row < 0:
        return
    ip_item   = self._table.item(row, _C_IP)
    host_item = self._table.item(row, _C_HOST)
    if not ip_item:
        return
    ip   = ip_item.text()
    host = host_item.text() if host_item else ''
    menu = HostActionMenu(ip, host, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

Dans `_build_ui`, après `layout.addWidget(self._table, ...)` :
```python
self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

- [ ] **Step 6: Test manuel**

- Scanner le réseau local → clic droit sur un hôte → toutes les actions disponibles
- "Voir en Topologie" → navigue vers Topology avec les hôtes découverts injectés (Topology.load_hosts doit être implémenté en Task 10)

- [ ] **Step 7: Commit**

```bash
git add nmlinux/pages/ip_scanner.py
git commit -m "feat: add source and _last_scan_hosts to IpScannerPage"
```

---

## Task 8 — Nmap : source + `_last_scan_hosts`

**Files:**
- Modify: `nmlinux/pages/nmap_scan.py`

**Interfaces:**
- Consumes: `HostActionMenu`, `ACT_*`
- Produces:
  - `NmapPage.action_requested = Signal(str, str, str)`
  - `NmapPage._last_scan_hosts: list[dict]` — agrégé par hôte
    - Chaque dict : `{'ip': str, 'hostname': str, 'ports': list[int]}`

Rappel : `row_ready` émet `{'host': "hostname (ip)" | ip, 'port': str, 'state': str, ...}`. Les colonnes sont `_COL_HOST=0, _COL_PORT=1, _COL_PROTO=2, _COL_STATE=3, _COL_SERVICE=4, _COL_VERSION=5`.

- [ ] **Step 1: Ajouter les imports**

```python
from nmlinux.core.host_actions import HostActionMenu
```

- [ ] **Step 2: Initialiser les structures dans `NmapPage.__init__`**

```python
self._last_scan_hosts: list[dict] = []
self._scan_agg: dict[str, dict] = {}  # host_label -> {ip, hostname, ports}
```

- [ ] **Step 3: Ajouter helper `_parse_host_label`**

```python
@staticmethod
def _parse_host_label(label: str) -> tuple[str, str]:
    """'hostname (1.2.3.4)' -> (ip, hostname); '1.2.3.4' -> (ip, '')"""
    import re
    m = re.match(r'^(.*)\s+\((\d+\.\d+\.\d+\.\d+)\)$', label)
    if m:
        return m.group(2), m.group(1).strip()
    return label, ''
```

- [ ] **Step 4: Accumuler dans `_on_row_ready` (ou équivalent)**

Chercher la méthode qui reçoit `row_ready` dans `NmapPage` (probablement `_on_row`). Elle reçoit un dict. Ajouter en début de cette méthode :

```python
def _on_row(self, data: dict) -> None:
    # Agrégation pour _last_scan_hosts
    host_label = data.get('host', '')
    if host_label not in self._scan_agg:
        ip, hostname = self._parse_host_label(host_label)
        self._scan_agg[host_label] = {'ip': ip, 'hostname': hostname, 'ports': []}
    try:
        port_num = int(data.get('port', ''))
        if data.get('state', '') == 'open':
            self._scan_agg[host_label]['ports'].append(port_num)
    except ValueError:
        pass
    # ... reste du code existant de la méthode
```

Dans la méthode qui reçoit `finished` (fin du scan) :
```python
self._last_scan_hosts = list(self._scan_agg.values())
self._scan_agg = {}
```

Dans la méthode `_scan` (début du scan), vider :
```python
self._scan_agg = {}
self._last_scan_hosts = []
```

- [ ] **Step 5: Ajouter signal + right-click**

```python
action_requested = Signal(str, str, str)

def _on_right_click(self, pos) -> None:
    row = self._table.rowAt(pos.y())
    if row < 0:
        return
    host_item = self._table.item(row, _COL_HOST)
    if not host_item:
        return
    host_label = host_item.text()
    ip, hostname = self._parse_host_label(host_label)
    # Récupérer les ports pour cette ligne (port de la ligne courante + connus)
    port_item = self._table.item(row, _COL_PORT)
    ports: list[int] = []
    if port_item:
        try:
            ports = [int(port_item.text())]
        except ValueError:
            pass
    if ip in self._scan_agg:
        ports = self._scan_agg[ip]['ports'] or ports
    menu = HostActionMenu(ip or host_label, hostname, ports or None, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

Dans `_build_ui`, après la création de `self._table` :
```python
self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

- [ ] **Step 6: Test manuel**

- Nmap scan mode "-sT fast" sur le réseau local → attendre les résultats → clic droit → SSH en gras si port 22 ouvert

- [ ] **Step 7: Commit**

```bash
git add nmlinux/pages/nmap_scan.py
git commit -m "feat: add source and _last_scan_hosts to NmapPage"
```

---

## Task 9 — SSH, RDP, VNC : cibles `set_target`

**Files:**
- Modify: `nmlinux/pages/ssh.py`
- Modify: `nmlinux/pages/rdp.py`
- Modify: `nmlinux/pages/vnc.py`

**Interfaces:**
- Produces:
  - `SshPage.set_target(ip: str, host: str = '') -> None`
  - `RdpPage.set_target(ip: str, host: str = '') -> None`
  - `VncPage.set_target(ip: str, host: str = '') -> None`

Rappel : les trois pages ont `_on_new()` → `_right.setCurrentIndex(_FORM)` avec les champs `self._f_host`, `self._f_name`, `self._f_port`.

- [ ] **Step 1: Ajouter `set_target` dans `SshPage`**

```python
def set_target(self, ip: str, host: str = '') -> None:
    self._on_new()           # réinitialise le formulaire et affiche _FORM
    self._f_host.setText(ip)
    if host and host != ip:
        self._f_name.setText(host)
```

- [ ] **Step 2: Ajouter `set_target` dans `RdpPage`**

```python
def set_target(self, ip: str, host: str = '') -> None:
    self._on_new()
    self._f_host.setText(ip)
    if host and host != ip:
        self._f_name.setText(host)
```

- [ ] **Step 3: Ajouter `set_target` dans `VncPage`**

```python
def set_target(self, ip: str, host: str = '') -> None:
    self._on_new()
    self._f_host.setText(ip)
    if host and host != ip:
        self._f_name.setText(host)
```

- [ ] **Step 4: Test manuel**

- IP Scanner → clic droit sur un hôte → "SSH" → naviguer vers SSH avec le formulaire "Nouvelle connexion" ouvert, IP prefillée
- Idem pour RDP et VNC

- [ ] **Step 5: Commit**

```bash
git add nmlinux/pages/ssh.py nmlinux/pages/rdp.py nmlinux/pages/vnc.py
git commit -m "feat: add set_target to SshPage, RdpPage, VncPage"
```

---

## Task 10 — Topology : source + cible `load_hosts`

**Files:**
- Modify: `nmlinux/pages/topology.py`

**Interfaces:**
- Consumes: `HostActionMenu`, `ACT_*`
- Produces:
  - `TopologyPage.action_requested = Signal(str, str, str)`
  - `TopologyPage.load_hosts(hosts: list[dict]) -> None`
    - Chaque dict doit avoir au minimum `'ip': str`; `'hostname'`, `'mac'`, `'vendor'` optionnels
  - `_NodeItem.node_action = Signal(str, str, list)` — (action_key, ip, ports) interne

Rappel : `_NodeItem.data` dict contient `'ip'`, `'hostname'`, `'type'`, `'device_class'`, `'vendor'`. Les nœuds sont créés via `_on_node(data)`.

- [ ] **Step 1: Ajouter l'import dans `topology.py`**

```python
from nmlinux.core.host_actions import HostActionMenu
```

- [ ] **Step 2: Ajouter `node_action` signal sur `_NodeItem` et `contextMenuEvent`**

Dans la classe `_NodeItem`, ajouter après la définition de la classe :

```python
# Dans _NodeItem (après les attributs de classe)
# PySide6 : Signal doit être défini sur la classe, pas l'instance
# On utilise un signal sur la vue/page via un workaround :
# _NodeItem émet via la scène → TopologyPage

def contextMenuEvent(self, event) -> None:  # noqa: N802
    ports = self.data.get('ports', [])
    ip    = self.data.get('ip', '')
    host  = self.data.get('hostname', '')
    # Remonter à TopologyPage via la scène
    scene = self.scene()
    if scene:
        views = scene.views()
        if views:
            page = views[0].property('topology_page')
            if page is not None:
                page._show_node_menu(ip, host, ports, event.screenPos())
    event.accept()
```

- [ ] **Step 3: Stocker la référence à `TopologyPage` sur la vue**

Dans `TopologyPage._build_ui`, après `self._view = _TopoView(self._scene)` :
```python
self._view.setProperty('topology_page', self)
```

- [ ] **Step 4: Ajouter `action_requested`, `_show_node_menu` et `load_hosts` dans `TopologyPage`**

```python
action_requested = Signal(str, str, str)

def _show_node_menu(self, ip: str, host: str, ports: list[int], screen_pos) -> None:
    menu = HostActionMenu(ip, host, ports or None, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(screen_pos.toPoint())

def load_hosts(self, hosts: list[dict]) -> None:
    if not hosts:
        return
    # Réinitialiser la scène
    self._scene_hint = None
    self._scene.clear()
    self._nodes.clear()
    self._gateway_node = None

    for data in hosts:
        node_data = {
            'ip':          data.get('ip', ''),
            'hostname':    data.get('hostname', ''),
            'mac':         data.get('mac', ''),
            'vendor':      data.get('vendor', ''),
            'type':        'host',
            'rtt':         0.0,
        }
        self._on_node(node_data)

    self._lbl_status.setText(f"{len(hosts)} hôtes importés depuis IP Scanner")
```

- [ ] **Step 5: Test manuel**

- IP Scanner → scanner le réseau → clic droit sur un hôte → "Voir en Topologie" → naviguer vers Topology avec les hôtes du scan déjà affichés comme nœuds
- Dans Topology → clic droit sur un nœud → menu contextuel → "Ping" → navigue vers Ping

- [ ] **Step 6: Commit**

```bash
git add nmlinux/pages/topology.py
git commit -m "feat: add Topology as source and load_hosts target"
```

---

## Task 11 — Asset Inventory : cible `prefill_hosts`

**Files:**
- Modify: `nmlinux/core/asset_collectors.py`
- Modify: `nmlinux/pages/asset_inventory.py`

**Interfaces:**
- Produces:
  - `AssetScanWorker(cidr, ssh_creds, winrm_creds, snmp_creds, hosts=None)` — paramètre optionnel
  - `AssetInventoryPage.prefill_hosts(hosts: list[dict]) -> None`
    - `hosts` : list de `{'ip': str, ...}` (format `_last_scan_hosts`)

- [ ] **Step 1: Modifier `AssetScanWorker.__init__` dans `asset_collectors.py`**

Trouver `def __init__(self, cidr: str, ...)` et ajouter le paramètre optionnel :

```python
def __init__(
    self,
    cidr: str,
    ssh_creds: list[dict],
    winrm_creds: list[dict],
    snmp_creds: dict,
    hosts: list[str] | None = None,   # ← nouveau paramètre
) -> None:
    super().__init__()
    self._cidr       = cidr
    self._hosts_override = hosts       # ← stocker
    # ... reste inchangé
```

- [ ] **Step 2: Modifier `AssetScanWorker.run` pour utiliser `_hosts_override`**

Dans `run()`, remplacer :
```python
hosts = [str(h) for h in ipaddress.ip_network(self._cidr, strict=False).hosts()]
```
par :
```python
if self._hosts_override is not None:
    hosts = self._hosts_override
else:
    try:
        hosts = [str(h) for h in ipaddress.ip_network(self._cidr, strict=False).hosts()]
    except ValueError:
        hosts = [self._cidr]
```

- [ ] **Step 3: Ajouter `prefill_hosts` dans `AssetInventoryPage`**

```python
def prefill_hosts(self, hosts: list[dict]) -> None:
    if not hosts:
        return
    ips = [h['ip'] for h in hosts if h.get('ip')]
    if not ips:
        return
    self._cidr.setText(', '.join(ips[:3]) + (f' … (+{len(ips)-3})' if len(ips) > 3 else ''))
    # Lancer le scan directement avec la liste
    ssh_creds    = self._get_ssh_creds()
    winrm_creds  = self._get_winrm_creds()
    snmp_creds   = self._get_snmp_creds()
    self._clear_results()
    self._worker = AssetScanWorker(
        '', ssh_creds, winrm_creds, snmp_creds,
        hosts=ips,
    )
    self._worker.host_found.connect(self._on_host_found)
    self._worker.finished.connect(self._on_finished)
    self._worker.start()
    self._btn_scan.setEnabled(False)
    self._btn_stop.setEnabled(True)
```

- [ ] **Step 4: Test manuel**

- IP Scanner → scanner → clic droit sur hôte → "Ajouter à l'inventaire" → navigue vers Asset Inventory avec scan lancé sur les hôtes découverts (phase ICMP skippée)

- [ ] **Step 5: Commit**

```bash
git add nmlinux/core/asset_collectors.py nmlinux/pages/asset_inventory.py
git commit -m "feat: add prefill_hosts to AssetInventory and optional host list to AssetScanWorker"
```

---

## Task 12 — Dashboard mini-widgets

**Files:**
- Modify: `nmlinux/pages/dashboard.py`
- Modify: `nmlinux/window.py`

**Interfaces:**
- Consumes: signal `watchlist_status_changed` de `TlsPage` (déjà existant)
- Produces:
  - `DashboardPage.set_tls_summary(status: str) -> None`
  - Worker interne `_GatewayPingWorker(QThread)`
  - Widget interne `_MiniPingGraph(QWidget)` — graphe 60 points, hauteur 60 px

- [ ] **Step 1: Ajouter `_GatewayPingWorker` dans `dashboard.py`**

Ajouter cette classe avant `DashboardPage` :

```python
class _GatewayPingWorker(QThread):
    rtt_ready = Signal(float)   # ms, ou -1.0 si timeout
    _running  = True

    def __init__(self, gateway: str) -> None:
        super().__init__()
        self._gateway = gateway

    def run(self) -> None:
        import time, re
        while self._running:
            try:
                proc = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', self._gateway],
                    capture_output=True, text=True, timeout=3,
                )
                if proc.returncode == 0:
                    m = re.search(r'time=(\d+\.?\d*)', proc.stdout)
                    self.rtt_ready.emit(float(m.group(1)) if m else 0.0)
                else:
                    self.rtt_ready.emit(-1.0)
            except Exception:
                self.rtt_ready.emit(-1.0)
            time.sleep(2)

    def stop(self) -> None:
        self._running = False
        self.quit()
```

- [ ] **Step 2: Ajouter `_MiniPingGraph` dans `dashboard.py`**

```python
class _MiniPingGraph(QWidget):
    _MAX = 60
    _H   = 60

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(self._H)
        self._data: list[float] = []   # ms, -1.0 = timeout

    def push(self, rtt: float) -> None:
        self._data.append(rtt)
        if len(self._data) > self._MAX:
            self._data.pop(0)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        valid = [v for v in self._data if v > 0]
        if not valid:
            return
        max_rtt = max(max(valid), 100.0)

        def _color(rtt: float) -> QColor:
            if rtt < 0:
                return QColor('#f38ba8')   # timeout rouge
            if rtt < 20:
                return QColor('#a6e3a1')   # vert
            if rtt < 100:
                return QColor('#fab387')   # orange
            return QColor('#f38ba8')       # rouge

        step = w / max(len(self._data), 1)
        pts  = []
        for i, rtt in enumerate(self._data):
            x = i * step + step / 2
            y = h - (max(rtt, 0) / max_rtt) * (h - 4) - 2 if rtt > 0 else h - 2
            pts.append((x, y, rtt))

        for x, y, rtt in pts:
            painter.setPen(QPen(_color(rtt), 2))
            painter.drawEllipse(QPointF(x, y), 2, 2)

        if len(pts) > 1:
            for i in range(len(pts) - 1):
                x1, y1, r1 = pts[i]
                x2, y2, r2 = pts[i + 1]
                if r1 > 0 and r2 > 0:
                    painter.setPen(QPen(_color(r1), 1))
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
```

- [ ] **Step 3: Modifier `DashboardPage.__init__` pour démarrer le worker ping**

```python
def __init__(self) -> None:
    super().__init__()
    self._worker: DashboardWorker | None = None
    self._ping_worker: _GatewayPingWorker | None = None
    self._build_ui()
    self._refresh()
    self._start_gateway_ping()
```

Ajouter la méthode :
```python
def _start_gateway_ping(self) -> None:
    import re, subprocess as _sp
    try:
        out = _sp.run(['ip', 'route', 'show', 'default'],
                      capture_output=True, text=True, timeout=3)
        m = re.search(r'via\s+(\S+)', out.stdout)
        gateway = m.group(1) if m else ''
    except Exception:
        gateway = ''
    if not gateway:
        return
    self._ping_worker = _GatewayPingWorker(gateway)
    self._ping_worker.rtt_ready.connect(self._mini_graph.push)
    self._ping_worker.start()

def stop_ping_worker(self) -> None:
    if self._ping_worker and self._ping_worker.isRunning():
        self._ping_worker.stop()
        self._ping_worker.wait(1000)
```

- [ ] **Step 4: Ajouter le mini-graphe et la carte TLS dans `_build_ui`**

Dans `DashboardPage._build_ui`, après la création de `self._box_gw` :

```python
# Mini-graphe ping gateway — inséré dans la carte gateway
self._mini_graph = _MiniPingGraph()
self._form_gw.addRow("Latence :", self._mini_graph)

# Carte TLS Watchlist
self._box_tls, self._form_tls = _card("TLS Watchlist")
self._lbl_tls = _val("—")
self._form_tls.addRow("Statut :", self._lbl_tls)
```

Ajouter `self._box_tls` dans la mise en page (ex : après `bot`) :
```python
vbox.addWidget(self._box_tls)
```

- [ ] **Step 5: Ajouter `set_tls_summary` dans `DashboardPage`**

```python
def set_tls_summary(self, status: str) -> None:
    if status == 'red':
        self._lbl_tls.setText("⚠ Alerte")
        self._lbl_tls.setStyleSheet(f"color: {color_err()};")
    elif status == 'orange':
        self._lbl_tls.setText("Expiration proche")
        self._lbl_tls.setStyleSheet("color: orange;")
    else:
        self._lbl_tls.setText("OK")
        self._lbl_tls.setStyleSheet(f"color: {color_ok()};")
```

- [ ] **Step 6: Câbler TLS → Dashboard dans `window.py`**

Dans `_build_stack`, après la connexion TLS existante (ligne ~384) :

```python
# TLS watchlist → Dashboard
dash_row = next((i for i, (_, lbl, _, _) in enumerate(_TOOLS) if lbl == "Dashboard"), -1)
if tls_row >= 0 and dash_row >= 0:
    tls_page  = self._pages[tls_row]
    dash_page = self._pages[dash_row]
    tls_page.watchlist_status_changed.connect(dash_page.set_tls_summary)
```

- [ ] **Step 7: Arrêter le worker ping dans `closeEvent` de `MainWindow`**

Dans `MainWindow.closeEvent` (ou en créer un s'il n'existe pas) :

```python
def closeEvent(self, event) -> None:
    dash_row = next((i for i, (_, lbl, _, _) in enumerate(_TOOLS) if lbl == "Dashboard"), -1)
    if dash_row >= 0:
        self._pages[dash_row].stop_ping_worker()
    super().closeEvent(event)
```

- [ ] **Step 8: Test manuel**

```bash
python -m nmlinux.main
```
- Dashboard → carte Gateway affiche le mini-graphe de latence qui se met à jour toutes les 2s
- TLS Inspector → ajouter un certificat en watchlist → observer que le Dashboard met à jour le statut TLS

- [ ] **Step 9: Commit**

```bash
git add nmlinux/pages/dashboard.py nmlinux/window.py
git commit -m "feat: add Dashboard gateway ping graph and TLS watchlist summary"
```

---

## Self-Review

**Couverture du spec :**
- ✅ `HostActionMenu` centralisé (Task 1)
- ✅ MainWindow routeur + auto-connect (Task 2)
- ✅ Pages sources : IP Scanner, Nmap, Ping, Traceroute, MTR, Port Scanner, DNS, Topology (Tasks 4-10)
- ✅ Pages cibles : Whois, DNS, Ping, Traceroute, MTR, Port Scanner, SSH, RDP, VNC, Topology, Asset Inventory (Tasks 3-11)
- ✅ `_last_scan_hosts` sur IP Scanner et Nmap (Tasks 7-8)
- ✅ Dashboard mini-graphe ping + TLS summary (Task 12)
- ✅ `_NodeItem` → signal interne → `TopologyPage` source (Task 10)
- ✅ `AssetScanWorker` avec hosts optionnels (Task 11)

**Types cohérents :**
- `action_requested = Signal(str, str, str)` — identique dans toutes les pages sources ✅
- `set_target(host)` vs `set_target(ip, host)` — SSH/RDP/VNC prennent deux args, les autres un ✅ (MainWindow routes utilisent les bonnes lambdas)
- `_last_scan_hosts: list[dict]` avec clé `'ip'` — cohérent entre IP Scanner (Task 7), Nmap (Task 8), et les consommateurs Topology (Task 10) et Asset Inventory (Task 11) ✅

**Note implémentation (Task 8 — Nmap):** La méthode qui reçoit `row_ready` dans `NmapPage` s'appelle probablement `_on_row` ou `_on_result` — vérifier le nom exact dans le fichier avant d'ajouter le code d'agrégation.

**Note implémentation (Task 11 — Asset Inventory):** Vérifier le nom exact des méthodes `_get_snmp_creds`, `_on_host_found`, `_on_finished` dans `asset_inventory.py` avant de les appeler dans `prefill_hosts`.
