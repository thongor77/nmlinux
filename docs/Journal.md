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
