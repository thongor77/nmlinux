# Carte des Modules

Chaque module = une page (`pages/*.py`) + son entrée dans `_TOOLS` (`window.py`).

## Légende

- **Backend** : outil système ou bibliothèque Python utilisé
- **Worker** : présence d'un QThread dédié
- **Persistence** : fichier JSON utilisateur
- **Export** : capacité d'export CSV/TXT
- **Root** : nécessite des privilèges élevés (pkexec ou sudo)

---

## 1 · Dashboard (`pages/dashboard.py` — 359 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ip route`, `ip addr`, `ip -j addr`, `resolvectl status`, `curl ifconfig.me`, `ip-api.com` |
| Worker | Oui (`_DashWorker`) |
| Persistence | — |
| Export | — |

Affiche : hostname, IPv4/IPv6 locale, masque réseau, passerelle, DNS résolveurs, IP publique, géolocalisation approximative.

---

## 2 · Connections (`pages/connection_manager.py` — 524 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `nmcli connection show`, `nmcli connection up/down/delete`, `nm-connection-editor` |
| Worker | Oui (`_ListWorker`, `_DetailWorker`, `_ActionWorker`) |
| Persistence | — (NetworkManager gère la sienne) |
| Export | — |

Filtre par type (Wi-Fi/Ethernet/VPN/WireGuard/Autre). Auto-refresh 5s (suspendu pendant une action).

---

## 3 · Interfaces (`pages/interfaces.py` — 246 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ip -j addr`, `nmcli device status` |
| Worker | Oui |
| Persistence | — |
| Export | — |

Colonnes : Interface / Type / État / MAC / IPv4 / IPv6. Panneau détail (masque réseau) au clic.

---

## 4 · Wi-Fi (`pages/wifi.py` — 266 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `nmcli dev wifi list` |
| Worker | Oui |
| Persistence | — |
| Export | — |

Signal affiché en barres ▂▄▆█. Réseau connecté en premier.

---

## 5 · Subnet (`pages/subnet.py` — 152 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ipaddress` (stdlib) |
| Worker | Non (calcul synchrone) |
| Persistence | — |
| Export | — |

Calcul CIDR → réseau, masque dotted, wildcard, broadcast, plage hôtes, total. IPv4 et IPv6.

---

## 6 · DNS (`pages/dns.py` — 234 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `dig` |
| Worker | Oui |
| Persistence | — |
| Export | — |

Types : A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Reverse lookup automatique depuis une IP. Serveur DNS configurable.

---

## 7 · Ping (`pages/ping.py` — 245 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ping` (ICMP) |
| Worker | Oui (un worker par hôte) |
| Persistence | — |
| Export | — |

Multi-hôtes simultanés. Intervalle 1–30s. Statistiques RTT min/avg/max, perte %.

---

## 8 · IP Scanner (`pages/ip_scanner.py` — 445 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ping -c 1 -W 1`, ARP cache, `getent hosts`, `avahi-resolve`, `nmblookup`, OUI DB interne |
| Worker | Oui, 50 threads |
| Persistence | — |
| Export | CSV + TXT |

Plage CIDR ou manuelle. Colonnes : IP / Hostname / MAC / Constructeur / Interface / État. Base OUI 39 000 entrées.

---

## 9 · Port Scanner (`pages/port_scanner.py` — 377 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `socket.connect_ex()` (TCP connect, sans root) |
| Worker | Oui, 200 threads |
| Persistence | — |
| Export | CSV + TXT |

Plages de ports, presets (Web, Mail, SSH…). Service identifié par port. Tri par port.

---

## 10 · Nmap (`pages/nmap_scan.py` — 325 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `nmap` (XML output parsé) |
| Worker | Oui |
| Persistence | — |
| Export | CSV + TXT |
| Root | Oui pour `-sS`, `-O`, `-A` |

7 modes : découverte (`-sn`), TCP (`-sT`), SYN (`-sS`), services (`-sV`), OS (`-O`), complet (`-A`), NSE. Résultats XML parsés en tableau structuré.

---

## 11 · Whois (`pages/whois.py` — 103 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `whois` subprocess |
| Worker | Oui |
| Persistence | — |
| Export | — |

Affichage brut monospace. Reverse lookup automatique depuis une IP.

---

## 12 · TLS Inspector (`pages/tls.py` — 501 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `openssl s_client` (subprocess) |
| Worker | Oui |
| Persistence | — |
| Export | — |

Affiche : CN, SANs, issuer, validité (vert/orange <30j/rouge expiré), serial, protocole, cipher, chaîne complète. Fonctionne avec certificats auto-signés et expirés.

---

## 13 · SMB / NFS (`pages/smb_nfs.py` — 271 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `smbclient -L` (SMB), `showmount -e` (NFS) |
| Worker | Oui |
| Persistence | — |
| Export | — |

Deux onglets. SMB : identifiants optionnels (utilisateur + mot de passe). NFS : export path + access list.

---

## 14 · Hosts File (`pages/hosts.py` — 319 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | Lecture directe `/etc/hosts`, écriture via `pkexec cp` |
| Worker | Non |
| Persistence | `/etc/hosts` (système) |
| Export | — |
| Root | Oui (pkexec pour l'écriture) |

Table avec toggle enable/disable, add/edit/delete via dialog. Filtre par IP ou hostname.

---

## 15 · SNMP (`pages/snmp.py` — 253 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `snmpwalk`, `snmpget` (net-snmp) |
| Worker | Oui |
| Persistence | — |
| Export | — |

v1/v2c. 10 presets OID (system, uptime, interfaces, CPU, mémoire…). Colonnes OID / Type / Valeur.

---

## 16 · SNTP / NTP (`pages/sntp.py` — 254 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | Client UDP pur Python (RFC 4330, socket) |
| Worker | Oui |
| Persistence | — |
| Export | — |

Pas de dépendance système. 1 à 5 requêtes moyennées. Affiche : offset, délai roundtrip, stratum, référence.

---

## 17 · SSH (`pages/ssh.py` — 678 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ssh` via PTY (`ptyprocess`), pyte VT100 |
| Worker | `SshWorker(QThread)` dans `core/terminal.py` |
| Persistence | `~/.local/share/nmlinux/ssh_connections.json` (v2) |
| Export | — |

Carnet d'adresses hiérarchique (groupes/sous-groupes). Auth clé ou mot de passe. Scrollback 2000 lignes. Toutes séquences VT100/xterm.

---

## 18 · SSH Keys (`pages/ssh_keys.py` — 527 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `ssh-keygen` (list, generate), `ssh-copy-id` |
| Worker | Oui |
| Persistence | `~/.ssh/` (détection des paires complètes) |
| Export | — |

Scan `~/.ssh/` (paires complètes uniquement). Génération Ed25519 / RSA 4096, passphrase optionnelle. Copie clé publique. Déploiement `ssh-copy-id` dans terminal inline.

---

## 19 · Remote Desktop (`pages/rdp.py` — 568 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `xfreerdp3` (Arch) ou `xfreerdp` (Debian/Ubuntu) |
| Worker | Non (Popen externe) |
| Persistence | `~/.local/share/nmlinux/rdp_connections.json` (v2) |
| Export | — |

Groupes/sous-groupes. Champs : host, port (3389), username, domain, résolution, fullscreen. Mot de passe jamais stocké.

---

## 20 · VNC (`pages/vnc.py` — 514 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `vncviewer` (TigerVNC) |
| Worker | Non (Popen externe) |
| Persistence | `~/.local/share/nmlinux/vnc_connections.json` (v2) |
| Export | — |

Groupes/sous-groupes. Port par défaut 5900. Format connexion : `host::port`. Compatible macOS ARD (DH30 géré nativement par vncviewer).

---

## 21 · Traceroute (`pages/traceroute.py` — 671 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `traceroute` ou `tracepath -b` (auto-détection), `ip-api.com` (géoloc) |
| Worker | `TracerouteWorker`, `GeolocWorker` (un par hop public) |
| Persistence | — |
| Export | CSV + TXT |

Carte monde interactive (Natural Earth 110m, `assets/world.geojson`). Projection équirectangulaire. Zoom molette, pan clic-glisser. Géoloc live par hop (IPs privées RFC-1918 skippées).

---

## 22 · MTR (`pages/mtr.py` — 455 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `mtr --report --report-cycles N` |
| Worker | Oui |
| Persistence | — |
| Export | CSV + TXT |

Tableau Hop / Host / Loss% / Sent / Last / Avg / Best / Worst / Jitter. Coloration loss% (vert<1% / jaune<10% / orange<25% / rouge≥25%). Parser texte regex (mtr 0.96 ignore `--json` en mode `--report`).

---

## 23 · Firewall (`pages/firewall.py` — 524 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | Lecture fichiers config (sans root) + `pkexec nft list ruleset` |
| Worker | Oui |
| Persistence | — |
| Export | — |
| Root | Oui (pkexec pour le ruleset live) |

Sources : `/etc/nftables.conf`, `/etc/iptables/iptables.rules`, `/etc/iptables/ip6tables.rules`. Colonnes : Table / Chain / Rule / Port / Action / Comment. Coloration : accept=vert / drop=rouge / reject=orange / jump·log=bleu.

---

## 24 · Speed Test (`pages/speedtest.py` — 605 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `curl` + `speed.cloudflare.com`, `ping 1.1.1.1` |
| Worker | Oui |
| Persistence | `~/.local/share/nmlinux/speedtest_history.json` (5 derniers) |
| Export | — |

Download 25 MB, Upload ~10 MB, Ping. Graphique line chart DL/UL horodaté.

---

## 25 · Bandwidth (`pages/bandwidth.py` — 373 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `/proc/net/dev` (lecture 1 Hz) |
| Worker | Non (QTimer dans le thread principal, < 1ms) |
| Persistence | — |
| Export | — |

Graphique glissant 60 secondes. Courbes download (bleu) / upload (orange). Sélection d'interface. Stats : vitesse live, total session, pics. Start/Stop explicite.

---

## 26 · Wake on LAN (`pages/wol.py` — 339 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `socket` UDP (Magic Packet natif Python, port 9) |
| Worker | Non |
| Persistence | `~/.local/share/nmlinux/wol_hosts.json` |
| Export | — |

Magic Packet : 6× `0xFF` + 16× adresse MAC. Broadcast configurable. Carnet d'hôtes (nom, MAC, broadcast).

---

## 27 · Topology (`pages/topology.py` — 609 lignes)

| Champ | Valeur |
|-------|--------|
| Backend | `nmap -sn -oX -` (XML), `ip route`, `ip -j addr` |
| Worker | `_TopoWorker` |
| Persistence | — |
| Export | — |

`QGraphicsScene` + `QGraphicsView`. Nœuds déplaçables (`ItemIsMovable`). Icônes dessinées : routeur (rect + antennes) / moniteur (écran + pied) / tour PC (rect + power). 1 ou 2 couronnes concentriques (seuil : 12 nœuds). Tooltip : hostname + IP + MAC + fabricant. `FullViewportUpdate` obligatoire (DashLine artifacts sinon).

---

## Pages hors _TOOLS

| Page | Fichier | Description |
|------|---------|-------------|
| Settings | `pages/settings.py` | Sélection langue + bannière redémarrage |
| About | `pages/about.py` | Crédits + version + outils tiers |
| Help | `pages/help_page.py` | Panneau aide contextuelle (badge `?`) |
