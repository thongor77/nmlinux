# Spec — Liens inter-modules + Dashboard mini-widgets

**Date :** 2026-07-02
**Version cible :** v1.7.0
**Statut :** approuvé

---

## Problème

Les modules de nmlinux fonctionnent en silos. Un hôte découvert dans IP Scanner ne peut pas être envoyé directement vers Port Scanner, Ping ou SSH. La Topology n'est pas reliée aux outils de connexion. Le Dashboard affiche un snapshot statique sans indication de l'état du réseau en temps réel.

---

## Solution

1. **Clic droit universel** sur toutes les tables contenant des IPs/hostnames — menu contextuel `HostActionMenu` permettant de naviguer vers n'importe quel module pertinent.
2. **Dashboard mini-widgets** passifs : mini-graphe ping gateway + résumé TLS Watchlist.

---

## Architecture

```
core/host_actions.py          ← HostActionMenu (QMenu réutilisable)
         ↓ Signal action_chosen(action_key, ip, host)
         ↓ (relayé par action_requested sur chaque page source)
MainWindow._on_host_action()  ← routeur central
         ↓ navigate_to(idx) + page.set_target(ip, host)
Pages cibles                  ← set_target() / load_hosts() / prefill_hosts()
```

Aucune page source ne connaît les pages cibles. Tout passe par MainWindow.

---

## Composant 1 — `nmlinux/core/host_actions.py`

### Classe `HostActionMenu(QMenu)`

```python
HostActionMenu(ip: str, host: str = '', ports: list[int] | None = None, parent=None)
```

- `ip` : adresse IP de l'hôte cible
- `host` : hostname (optionnel, affiché dans le titre du menu)
- `ports` : liste des ports ouverts détectés (optionnel) — sert au highlighting

### Structure du menu

```
─── Naviguer vers ───
  Ping
  Scanner les ports
  Whois
  DNS
  Traceroute
  MTR
─── Connexion ───
  SSH          ← gras si 22 dans ports
  RDP          ← gras si 3389 dans ports
  VNC          ← gras si 5900 dans ports
─── Inventaire ───
  Voir en Topologie
  Ajouter à l'inventaire
```

Les trois sections sont toujours présentes, quelle que soit la disponibilité de `ports`.
Quand `ports` est fourni, les entrées SSH/RDP/VNC dont le port est détecté sont affichées en **gras** (signal visuel, pas filtre).

Labels via `tr()` pour i18n future.

### Signal

```python
action_chosen = Signal(str, str, str)  # (action_key, ip, host)
```

### Constantes d'action

```python
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
```

---

## Composant 2 — Pages sources

### Signal commun

Toutes les pages sources exposent :

```python
action_requested = Signal(str, str, str)  # (action_key, ip, host)
```

### Pattern d'implémentation (identique pour toutes les pages sources)

```python
def _on_right_click(self, pos):
    row = self._table.rowAt(pos.y())
    if row < 0:
        return
    ip, host, ports = self._get_row_data(row)
    menu = HostActionMenu(ip, host, ports, parent=self)
    menu.action_chosen.connect(self.action_requested)
    menu.exec(self._table.viewport().mapToGlobal(pos))
```

`_get_row_data(row) -> (ip, host, ports | None)` est propre à chaque page.

Le handler right-click est installé via :
```python
self._table.setContextMenuPolicy(Qt.CustomContextMenu)
self._table.customContextMenuRequested.connect(self._on_right_click)
```

### Pages sources et données disponibles

| Page | Colonnes disponibles | ports fournis ? |
|------|---------------------|-----------------|
| IP Scanner | IP, hostname, MAC, vendor, RTT | Non (sauf si nmap activé) |
| Port Scanner | host, port, service, RTT | Oui (ports ouverts de la ligne) |
| Nmap | host, port, proto, state, service, version | Oui (ports de l'hôte) |
| Ping | host, RTT, status | Non |
| Traceroute | hop, IP, hostname, RTT | Non |
| MTR | hop, IP, hostname, loss%, RTT | Non |
| DNS | (IPs dans les résultats uniquement) | Non |

### Topology — cas particulier

Le right-click se passe sur `_NodeItem(QGraphicsItem)`, pas sur une `QTableWidget`.

`_NodeItem` émet un signal interne `node_action = Signal(str, str, list)` (action_key, ip, ports) capté par `TopologyPage`. C'est `TopologyPage` qui crée le `HostActionMenu` (depuis `mousePressEvent` ou `contextMenuEvent` sur la vue) et émet son propre `action_requested = Signal(str, str, str)` vers MainWindow — identique aux autres pages sources.

Ce découplage évite que `_NodeItem` ait besoin d'une référence à MainWindow.

---

## Composant 3 — MainWindow : connexions et routeur

### Connexion automatique dans `_build_stack`

```python
for page in self._pages:
    if hasattr(page, 'action_requested'):
        page.action_requested.connect(self._on_host_action)
```

Une seule ligne — pas de connexion explicite par page.

### Routeur `_on_host_action`

```python
def _on_host_action(self, action: str, ip: str, host: str) -> None:
    target = host or ip
    routes = {
        ACT_PING:       (self._page_index('PingPage'),
                         lambda p: p.set_target(target)),
        ACT_PORT_SCAN:  (self._page_index('PortScannerPage'),
                         lambda p: p.set_target(ip)),
        ACT_WHOIS:      (self._page_index('WhoisPage'),
                         lambda p: p.set_target(target)),
        ACT_DNS:        (self._page_index('DnsPage'),
                         lambda p: p.set_target(target)),
        ACT_TRACEROUTE: (self._page_index('TraceroutePage'),
                         lambda p: p.set_target(target)),
        ACT_MTR:        (self._page_index('MtrPage'),
                         lambda p: p.set_target(target)),
        ACT_SSH:        (self._page_index('SshPage'),
                         lambda p: p.set_target(ip, host)),
        ACT_RDP:        (self._page_index('RdpPage'),
                         lambda p: p.set_target(ip, host)),
        ACT_VNC:        (self._page_index('VncPage'),
                         lambda p: p.set_target(ip, host)),
        ACT_TOPOLOGY:   (self._page_index('TopologyPage'),
                         lambda p: p.load_hosts(self._pending_hosts)),
        ACT_ASSET:      (self._page_index('AssetInventoryPage'),
                         lambda p: p.prefill_hosts(self._pending_hosts)),
    }
    if action not in routes:
        return
    idx, fn = routes[action]
    fn(self._pages[idx])
    self.navigate_to(idx)
```

`_page_index(class_name)` retourne l'index dans `self._pages` en cherchant par `type(page).__name__`.

Pour `ACT_TOPOLOGY` et `ACT_ASSET`, la page source stocke la liste de hosts dans `self._last_scan_hosts: list[dict]` après chaque scan. Quand MainWindow reçoit le signal, elle identifie la page émettrice via `self.sender()` et lit `sender._last_scan_hosts` pour le passer à la page cible. Cela évite tout état partagé dans MainWindow.

---

## Composant 4 — Pages cibles : contrat `set_target`

| Page | Signature | Comportement |
|------|-----------|-------------|
| Ping | `set_target(host: str)` | Prefill + lance ping automatiquement |
| Port Scanner | `set_target(ip: str)` | Prefill + focus bouton Scan (ne lance pas) |
| Whois | `set_target(target: str)` | Prefill + déclenche requête immédiatement |
| DNS | `set_target(host: str)` | Prefill uniquement (type d'enregistrement au choix) |
| Traceroute | `set_target(host: str)` | Prefill + lance immédiatement |
| MTR | `set_target(host: str)` | Prefill + lance immédiatement |
| SSH | `set_target(ip: str, host: str = '')` | Ouvre formulaire nouvelle connexion prefillé, ne connecte pas |
| RDP | `set_target(ip: str, host: str = '')` | Idem |
| VNC | `set_target(ip: str, host: str = '')` | Idem |
| Topology | `load_hosts(hosts: list[dict])` | Injecte les nœuds sans re-scanner |
| Asset Inventory | `prefill_hosts(ips: list[str])` | Saute la phase de scan ICMP |

**Règle :** `set_target` ne lance jamais de réseau si le résultat est destructif ou long (Port Scanner, DNS, SSH/RDP/VNC). Il lance automatiquement si le résultat est rapide et non-destructif (Ping, Whois, Traceroute, MTR).

---

## Composant 5 — Dashboard mini-widgets

### Mini-graphe ping gateway

**Worker :** `_GatewayPingWorker(QThread)` dans `dashboard.py`
- Lit la gateway via `ip route` au démarrage (déjà disponible dans `_collect_local()`)
- Ping toutes les 2 secondes via `subprocess.run(['ping', '-c', '1', '-W', '1', gateway])`
- Émet `rtt_ready = Signal(float)` — valeur en ms, `-1.0` si timeout

**Seuils de couleur :**
- < 20 ms → `color_ok` (vert)
- 20–100 ms → orange
- > 100 ms → rouge
- timeout → rouge plein

**Graphe :** `_MiniPingGraph(QWidget)` — même moteur QPainter que `BandwidthGraph`, `deque(maxlen=60)`, hauteur fixe 60 px dans la carte Dashboard.

**Cycle de vie :** démarre dans `DashboardPage.__init__`, s'arrête dans `MainWindow.closeEvent`.

### Résumé TLS Watchlist

`TlsPage` émet déjà `watchlist_status_changed(status: str)` (capté par la sidebar).

MainWindow connecte ce signal également vers `DashboardPage.set_tls_summary(status: str)`.

`status` : `""` = OK, `"orange"` = expiration proche (< 30 j), `"red"` = expiré ou UNTRUSTED.

Dashboard affiche dans sa carte résumé : `TLS Watchlist : X certificats — Y alerte(s)` avec couleur correspondante. Pas de re-calcul côté Dashboard.

---

## Fichiers créés ou modifiés

| Fichier | Nature |
|---------|--------|
| `nmlinux/core/host_actions.py` | **Nouveau** — HostActionMenu + constantes ACT_* |
| `nmlinux/window.py` | Modifié — connexion auto, `_on_host_action`, `_page_index`, dashboard wiring |
| `nmlinux/pages/ip_scanner.py` | Modifié — `action_requested` signal + right-click |
| `nmlinux/pages/port_scanner.py` | Modifié — source + cible (`set_target`) |
| `nmlinux/pages/nmap_scan.py` | Modifié — source |
| `nmlinux/pages/ping.py` | Modifié — source + cible (`set_target`) |
| `nmlinux/pages/traceroute.py` | Modifié — source + cible (`set_target`) |
| `nmlinux/pages/mtr.py` | Modifié — source + cible (`set_target`) |
| `nmlinux/pages/dns.py` | Modifié — source + cible (`set_target`) |
| `nmlinux/pages/topology.py` | Modifié — source (`_NodeItem.contextMenuEvent`) + cible (`load_hosts`) |
| `nmlinux/pages/whois.py` | Modifié — cible (`set_target`) |
| `nmlinux/pages/ssh.py` | Modifié — cible (`set_target`) |
| `nmlinux/pages/rdp.py` | Modifié — cible (`set_target`) |
| `nmlinux/pages/vnc.py` | Modifié — cible (`set_target`) |
| `nmlinux/pages/asset_inventory.py` | Modifié — cible (`prefill_hosts`) |
| `nmlinux/pages/dashboard.py` | Modifié — `_GatewayPingWorker`, `_MiniPingGraph`, `set_tls_summary` |

---

## Hors périmètre

- Internationalisation des labels du menu (infrastructure `tr()` posée, traductions en v1.7.x)
- Tests automatisés
- Montage SMB/NFS (spec séparée)
- Firewall en écriture (roadmap future)
