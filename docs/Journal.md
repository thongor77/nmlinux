# Journal de développement

Les entrées détaillées sont dans la note Obsidian `~/Obsidian/MyVault/Projets/nmlinux.md`.
Ce fichier reprend les jalons techniques essentiels.

---

## 2026-05-09 — Lancement

- Création du projet Python/PySide6 — abandon du portage .NET/Avalonia (artefacts GPU Wayland).
- 13 modules initiaux.

## 2026-05-14 — Repo GitHub + i18n

- Publication https://github.com/thongor77/nmlinux
- i18n 4 langues (fr/en/es/de), `core/i18n.py`, `core/settings.py`, `core/icons.py`

## 2026-05-15 — Terminal SSH

- Migration `QPlainTextEdit + strip_ansi` → `pyte.HistoryScreen + QPainter` (7 commits de correctifs, puis refonte complète).
- `SshWorker` émet bytes bruts, `TerminalView` gère tout via pyte.

## 2026-05-16 — v1.1.1

- Traceroute visuel (carte monde Natural Earth), Bandwidth Monitor, scrollback 2000 lignes.
- Publication AUR.

## 2026-05-22 — v1.2.0

- Thème clair/sombre runtime (`core/theme.py`).
- Masque réseau dans Dashboard/Interfaces/Connections.
- Exports CSV/TXT Nmap + Traceroute.

## 2026-05-23 — v1.2.5

- MTR, Speed Test (curl + Cloudflare), Firewall.
- Sidebar : badge `?` + tooltips (23 entrées).

## 2026-05-26 — v1.2.7

- Icônes Lucide bundlées → suppression dépendance thème système.

## 2026-05-30 — v1.2.8 + v1.2.9

- Remote Desktop (RDP) + VNC.
- Sidebar labels EN, 23 tooltips i18n.

## 2026-06-03 — v1.3.0

- TLS Inspector, SMB/NFS Browser, Hosts File Editor.
- `install.sh` pour Debian/Ubuntu/Mint.

## 2026-06-05 — v1.3.1

- SSH Key Manager (génération Ed25519/RSA, ssh-copy-id, suppression).
- Aide contextuelle (`pages/help_page.py` + `core/help_content.py`).
- 49 étoiles GitHub.

## 2026-06-06 — v1.3.5

- Compatibilité macOS : 9 modules dual Linux/macOS via `_IS_MACOS` + commandes natives.
- Modules couverts : Dashboard, Interfaces, Wi-Fi, Topology, Bandwidth, Firewall (pf), Connection Manager, Hosts, MTR.
- Firewall : parser `parse_pf()`, `LiveRulesetWorkerMacos`, sources dynamiques selon OS.
- Connection Manager : `_ListWorkerMacos`, `_DetailWorkerMacos`, actions via `osascript`.

## 2026-06-06 — v1.3.2

- i18n 4 → 8 langues (+Italiano +Português +日本語 +中文).
- Aide contextuelle : 8 langues × 27 modules.
- Fix : `nav_hint_smb_nfs` + `nav_hint_hosts` manquants dans 7 blocs non-fr.
- **Bug documenté :** injection programmatique — `ja` s'imbriquait dans `pt` (syntaxe valide mais sémantique incorrecte). Voir DT-13 dans Decisions-Techniques.md.

## 2026-06-25 — v1.6.1

- **Fix terminal SSH — écho distant** : sur VM Ubuntu 26.04 fraîche, le clavier semblait « mort » après l'auth (frappes envoyées au shell distant mais jamais ré-affichées). `SshWorker` forçait l'écho off (`echo=False` + `_kill_echo()`), et ssh propageait ce « no echo » au pty distant via les modes du `pty-req`. Fix : spawn `echo=True`, suppression de `_kill_echo()`/`_echo_checks` — on laisse ssh gérer les modes, comme un vrai émulateur. Voir DT-14.

## 2026-07-02 — v1.7.0 + v1.7.1

- **Liens inter-modules** : `HostActionMenu` + pattern `set_target()`/`source` généralisé à IP Scanner, Nmap, Topology, Ping, DNS, Whois, Port Scanner, SSH, RDP, VNC et Asset Inventory — clic droit sur un hôte déclenche l'action et navigue vers le module cible.
- Dashboard : mini-graph de ping vers la gateway (réutilise le moteur QPainter de Bandwidth Monitor) + résumé TLS Watchlist.
- Suppression des dernières références à BornToBeRoot/NETworkManager dans le code et la doc.
- **Compat macOS 26** : passage à CoreWLAN pour le SSID Wi-Fi (Location Services désormais requises), fix crash à la fermeture (relâchement de la référence `CLLocationManager`), fix parsing MAC ARP (octets courts non zéro-paddés), auto-download de la base OUI + hostname mDNS via `dns-sd`.
- Script bootstrap macOS en one-liner : téléchargement puis exécution locale, au lieu d'un pipe direct `curl | bash`.

## 2026-07-03 — v1.7.2 + v1.7.3

- SMB ajouté au menu contextuel universel (clic droit sur un hôte).
- i18n Dashboard complété (latence, carte TLS, statut) — dernières chaînes non traduites.
- **Montage SMB/NFS depuis l'interface** : `mount()`/`unmount()` Linux + macOS, clic droit sur l'onglet SMB, montage persistant via unit systemd `.mount`, authentification `pkexec` unique (au lieu de deux appels), retry automatique avec un dialecte SMB plus ancien sur erreur `ENOTSUPP`, fix crash si le point de montage ne peut être créé. Dépendance optionnelle `cifs-utils`.

## 2026-07-04 — v1.7.4 + v1.7.5

- Fix scans Asset Inventory instables ; ajout d'un bouton "Relancer sur les IP vides".
- Ping Monitor : répertoire de cibles sauvegardées (`PingTarget` + `_PingTargetStore`), bouton pour sauvegarder une cible active depuis une ligne en cours, i18n 8 langues.

## 2026-07-05 — v1.7.6

- Asset Inventory : clic droit pour rescanner une sélection de lignes en place (dédoublonnage par IP au lieu d'ajouter une nouvelle ligne à chaque rescan).
- Échec d'authentification SSH désormais affiché dans le tableau (`SSH auth failed`) au lieu d'un fallback silencieux vers les seules données Nmap ; correctif de suivi pour ne pas laisser cet échec écraser la méthode/OS déjà détectés par Nmap.

## 2026-07-14 — v1.7.8

- **Speed Test — onglet LAN (iperf3)** : suite à la feature request GitHub #6 (`loren2018tw`), nouveau test de débit point-à-point via `iperf3` (client uniquement), en complément du test internet existant. Choix entre une liste de 26 serveurs publics bundlée par pays et des serveurs personnalisés sauvegardés. TCP/UDP, IPv4/IPv6/auto, sens (reverse = download). Voir DT-15.
- Découverte et correction en passant d'un trou i18n préexistant : le bloc allemand n'avait aucune clé `speed_*`/`mtr_*`/`fw_*` (56 clés), comblées dans le même commit.
- Nouvelle dépendance optionnelle : `iperf3`.
