# Roadmap NMLinux

## Version courante : v1.7.6 (2026-07-05)

29 modules, 8 langues UI, aide contextuelle 8 langues × 28 modules (File Transfer non couvert), compatibilité Linux + macOS (macOS 26 inclus), Asset Inventory (SSH/WinRM/SNMP), liens inter-modules (clic droit → Ping/DNS/Whois/Port Scanner/SSH/RDP/VNC/Asset Inventory/Topology), montage SMB/NFS, AppImage + macOS .app.

---

## Candidats vérifiés (mentionnés explicitement par l'utilisateur)

Ces idées ont été discutées et validées — elles ne sont pas encore implémentées.

### ~~Liens inter-modules~~ — LIVRÉ en v1.7.0

> Implémenté en v1.7.0 (2026-07-02). Voir historique ci-dessous pour référence.

<details>
<summary>Spécification originale (archivée)</summary>

**Principe général :** pattern Signal → MainWindow → `set_target()` déjà posé par TLS Watchlist → sidebar. Couplage nul entre les pages elles-mêmes.

#### Liens prioritaires

| Source | Cible | Déclencheur | Bénéfice |
|--------|-------|-------------|----------|
| IP Scanner | Port Scanner | Clic droit sur host → "Scanner les ports" | Workflow naturel découverte → analyse |
| IP Scanner | Ping | Clic droit → "Pinger" | Idem |
| IP Scanner | Whois | Clic droit → "Whois" | Idem |
| IP Scanner | Topology | Bouton "Voir en topologie" | Réutilise les nœuds déjà découverts |
| IP Scanner | Asset Inventory | Bouton "Inventorier" | Saute la phase de re-scan |
| Topology | SSH / RDP / VNC | Clic droit sur nœud → connect | Auto-détecte le protocole via ports ouverts |
| Topology | Ping / Port Scanner | Clic droit sur nœud | Navigation directe depuis la carte |
| Dashboard | Ping gateway (mini-graph) | Passif, en fond | Réutilise le moteur QPainter Bandwidth |
| Dashboard | TLS Watchlist résumé | Passif | Données déjà calculées, juste afficher N certs |

#### Implémentation type (IP Scanner → Port Scanner)
- `IpScannerPage` : `host_activated = Signal(str)` — émis au clic droit → action
- `PortScannerPage` : `set_target(ip: str)` — prefill le champ host + focus
- `MainWindow._build_stack` : connecte le signal + appelle `navigate_to(idx_port_scanner)`

</details>

---

### ~~SMB/NFS — montage depuis l'interface~~ — LIVRÉ en v1.7.3

> Implémenté en v1.7.3 (2026-07-03). Voir historique ci-dessous pour référence.

<details>
<summary>Spécification originale (archivée)</summary>

Actuellement nmlinux liste les partages (smbclient / showmount) sans pouvoir monter.

**Approche :** même pattern que `hosts.py` — `pkexec` pour l'élévation, logique de montage inspirée de `netmnt/crates/netmntd/src/exec.rs` (projet parallèle), sans requérir que netmnt soit installé.

- **Session mount** : `pkexec mount.cifs //host/share /mount/point -o rw,uid=X,username=U`, mot de passe via variable d'environnement `PASSWD` (jamais en argument CLI)
- **Persistent mount** : générer une unit systemd `.mount` + fichier credentials chmod 600 + `systemctl enable --now`
- **Unmount** : détecter si unit systemd active → `systemctl disable --now` + cleanup, sinon `umount` direct
- **NFS** : `pkexec mount -t nfs host:/export /mount/point`
- **UI** : bouton "Monter" sur la ligne sélectionnée, dialogue choix du point de montage (session / persistant), liste des montages actifs avec bouton "Démonter"

</details>

---

### ~~Asset Inventory~~ — LIVRÉ en v1.6.0

> Implémenté en v1.6.0 (2026-06-24). Voir historique ci-dessous pour référence.

<details>
<summary>Spécification originale (archivée)</summary>

### Asset Inventory (v1.6.x)

Inspiré de LanSweeper mais volontairement léger — pas de base de données, pas d'agents, pas de collecte continue.

**Principe** : scan réseau → pour chaque hôte découvert, collecte d'infos selon la méthode disponible (sans credentials ou avec). Toutes les données sont **purement éphémères** : rien n'est écrit sur disque, tout est effacé à la fermeture de l'application.

---

#### Détection sans credentials

- Scan CIDR (moteur IP Scanner existant)
- OS fingerprint via Nmap `-O`
- Ports ouverts, services détectés (`-sV`)
- Hostname (DNS/mDNS/NetBIOS), MAC address, vendor OUI
- Plateforme probable déduite (Linux/Windows/macOS/Network device) à partir des ports ouverts et bannières

---

#### Collecte avec credentials

##### Linux / macOS — via SSH

- Credentials : username + password ou clé privée (champ echoMode=Password, jamais stocké)
- Commandes exécutées à distance : `uname -a`, `lsb_release -a`, `/proc/cpuinfo`, `free -h`, `df -h`, `uptime`
- Collecte : OS exact, distribution, version kernel, CPU (modèle, cœurs), RAM totale/libre, disques (point de montage, taille, usage %), uptime

##### Windows — via WinRM

- Dépendance : `pywinrm` (`pip install pywinrm`)
- Credentials : username + password (domaine optionnel), jamais stockés
- Transport : HTTP (port 5985) ou HTTPS (port 5986)
- Données collectées via PowerShell distant :
  - OS : `Get-WmiObject Win32_OperatingSystem` → Caption, Version, BuildNumber
  - CPU : `Get-WmiObject Win32_Processor` → Name, NumberOfCores
  - RAM : `Win32_PhysicalMemory` → capacité totale
  - Disques : `Get-WmiObject Win32_LogicalDisk` → DriveType=3, Size, FreeSpace
  - Uptime : `LastBootUpTime`
- Prérequis côté Windows : WinRM activé (`winrm quickconfig`)

##### Équipements réseau — via SNMP

- SNMP v1/v2c : adresse + communauté (champ texte, jamais stocké)
- SNMP v3 : adresse + username + authPassword + privPassword, protocoles authProtocol (MD5/SHA) et privProtocol (DES/AES) — champs echoMode=Password, jamais stockés
- OIDs collectés : sysDescr (1.3.6.1.2.1.1.1.0), sysName (1.3.6.1.2.1.1.5.0), sysUpTime (1.3.6.1.2.1.1.3.0), sysContact, sysLocation
- Cibles typiques : switches, routeurs, NAS, imprimantes, UPS

---

#### Interface

- **Tableau assets** : IP / Hostname / Plateforme / OS / CPU / RAM / Disques / Uptime / Méthode (`—` / SSH / WinRM / SNMP)
- **Panneau credentials** : saisie par protocole (SSH / WinRM / SNMP), appliqués à tous les hôtes du scan ou par hôte individuel
- **Scan progressif** : barre de progression, résultats qui s'affichent au fur et à mesure
- **Export** : JSON / CSV / Markdown — déclenché manuellement par l'utilisateur

---

#### Politique de rétention — zéro persistance

**Exigence explicite (session 2026-06-24) : aucune donnée ne doit survivre à la fermeture de l'application.**

- Aucun fichier écrit automatiquement sur disque (ni assets, ni credentials, ni cache)
- Toutes les données résident uniquement en RAM (structures Python in-process)
- Credentials : jamais sérialisés, jamais logués, effacés (`del`) immédiatement après usage
- `closeEvent` de MainWindow → `clear()` explicite de toutes les structures de données du module
- Export JSON/CSV/Markdown : uniquement à la demande explicite de l'utilisateur — c'est son choix, pas un comportement automatique
- Aucun fichier temporaire laissé dans `/tmp` ou ailleurs

---

#### Ce que ce n'est pas

Pas de scheduler, pas de base SQL, pas de CMDB, pas d'inventaire logiciel complet, pas d'alerting. C'est un outil de reconnaissance réseau enrichi à la demande.

---

**Cohérence avec nmlinux :** réutilise IP Scanner, SNMP, SSH existants. S'intègre naturellement dans la sidebar.

</details>

---

## Idées futures (direction validée, pas encore spécifiées)

### Firewall — mode écriture

Le module Firewall est actuellement en lecture seule (affichage nft/iptables/pf). Direction validée : ajouter l'écriture.

**Axes à spécifier avant implémentation :**
- Ajout/suppression de règles via GUI (nft et iptables)
- Recherche/filtre par port, IP, action
- Export des règles en script shell
- Périmètre : nft uniquement d'abord (nftables est le standard moderne sur Arch/Debian/Ubuntu), iptables en option

**Contrainte :** élévation de privilège requise pour toute modification — pkexec ou sudo selon la distribution.

---

## Idées évoquées sans décision formelle

⚠️ Ces éléments ont été mentionnés mais pas actés. **Ne pas implémenter sans confirmation.**

### ~~WifiMapper~~ — LIVRÉ comme projet indépendant

> Implémenté sous le nom **WifiMapLinux** dans `/home/luust/claude-projects/WifiMapLinux/` — projet distinct, hors scope nmlinux.

### nmlinux-tui

- Version terminal (SSH-friendly) du même outil
- Implémentée séparément : https://github.com/thongor77/nmlinux-tui
- 5 écrans Textual, dashboard 3 panels, 27 tests

---

## Modules complétés par version

| Version | Date | Ajouts principaux |
|---------|------|-------------------|
| v1.0.0 | 2026-05-14 | 13 modules, SSH hiérarchique, i18n fr/en/es/de, GitHub |
| v1.1.1 | 2026-05-16 | Terminal pyte+QPainter, Traceroute visuel, Bandwidth |
| v1.2.0 | 2026-05-22 | Thème clair/sombre, masque réseau, exports CSV/TXT |
| v1.2.5 | 2026-05-23 | MTR, Speed Test, Firewall, sidebar hints |
| v1.2.6 | 2026-05-24 | Compat GNOME + NixOS |
| v1.2.7 | 2026-05-26 | Icônes Lucide bundlées |
| v1.2.8 | 2026-05-30 | Remote Desktop (RDP) |
| v1.2.9 | 2026-05-30 | VNC, About outils, sidebar i18n, 23 tooltips |
| v1.3.0 | 2026-06-03 | TLS Inspector, SMB/NFS, Hosts File, install.sh Debian/Ubuntu/Mint |
| v1.3.1 | 2026-06-05 | SSH Key Manager, aide contextuelle (help_page.py) |
| v1.3.2 | 2026-06-06 | i18n 8 langues (+ it/pt/ja/zh), aide contextuelle 8 langues × 27 modules |
| v1.3.5 | 2026-06-06 | Compatibilité macOS — 9 modules dual Linux/macOS, MACOS_PORTING.md |
| v1.3.6 | 2026-06-08 | Fix Ubuntu 26.04 (freerdp3-x11, pipx system deps) |
| v1.3.7 | 2026-06-12 | Topology : icônes précises 7 classes d'appareil via vendor OUI |
| v1.3.8 | 2026-06-13 | Command Palette (Ctrl+P), Export Manager (JSON/MD/TXT/PDF), boutons export DNS/Firewall/SSH/Connections |
| v1.4.0 | 2026-06-13 | SSH agent forwarding, badges README shields.io (version/python/license/platform/languages) |
| v1.4.1 | 2026-06-14 | IP Scanner macOS : ARP via `arp -n`, VNC server note × 8 langues |
| v1.4.2 | 2026-06-14 | TLS Watchlist : dot rouge/orange dans sidebar, fichier de config persistant |
| v1.4.3 | 2026-06-14 | TLS Watchlist : détection UNTRUSTED (cert invalide / chaîne brisée) |
| v1.5.0 | 2026-06-17 | Module File Transfer (serveur TFTP + serveur HTTP GET/POST), AppImage 93 Mo |
| v1.5.1 | 2026-06-18 | Fix HTTP download macOS (URL encoding), fix couleurs map traceroute |
| v1.5.2 | 2026-06-19 | macOS .app bundle : install_macos_app.sh + uninstall_macos.sh + icône .icns auto-générée |
| v1.6.0 | 2026-06-24 | Asset Inventory : SSH Linux/macOS/Unraid + WinRM Windows (EncodedCommand base64) + SNMP |
| v1.6.1 | 2026-06-25 | Fix écho terminal SSH (echo PTY géré par ssh, DT-14) |
| v1.6.2 | 2026-06-28 | Fix macOS menu bar "Python" → NSBundle.infoDictionary patch |
| v1.6.4 | 2026-06-28 | Fix macOS menu bar : fallback AppKit robuste, stabilisation |
| v1.7.0 | 2026-07-02 | Liens inter-modules (IP Scanner/Nmap/Topology → Ping/DNS/Whois/Port Scanner/SSH/RDP/VNC/Asset Inventory via `HostActionMenu`), Dashboard : mini-graph ping gateway + résumé TLS Watchlist |
| v1.7.1 | 2026-07-02 | Compat macOS 26 : CoreWLAN pour SSID Wi-Fi (Location Services), fix crash à la fermeture, script bootstrap one-liner |
| v1.7.2 | 2026-07-03 | SMB ajouté au menu contextuel universel, i18n Dashboard complet |
| v1.7.3 | 2026-07-03 | SMB/NFS : montage/démontage via `pkexec` (session + persistant via unit systemd) |
| v1.7.4 | 2026-07-04 | Fix scans Asset Inventory instables, bouton "Relancer sur les IP vides" |
| v1.7.5 | 2026-07-04 | Ping Monitor : répertoire de cibles sauvegardées (ajout/relance depuis les lignes actives) |
| v1.7.6 | 2026-07-05 | Asset Inventory : clic-droit "Actualiser la sélection", feedback échec d'authentification SSH au lieu d'un fallback silencieux |
