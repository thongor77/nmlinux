# Roadmap NMLinux

## Version courante : v1.3.5 (2026-06-06)

27 modules, 8 langues UI, aide contextuelle 8 langues × 27 modules, compatibilité macOS.

---

## Candidats vérifiés (mentionnés explicitement par l'utilisateur)

Ces idées ont été discutées et validées — elles ne sont pas encore implémentées.

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

**Priorité :** validé par l'utilisateur en session 2026-06-24 — à planifier après stabilisation v1.5.x.

---

### Générateur de mots de passe

- Module standalone (pas de page réseau)
- Backend : `secrets` (stdlib)
- Fonctionnalités discutées : longueur configurable, jeux de caractères, affichage entropie en bits, bouton Copier
- Priorité : mentionné comme "prochaine étape candidate" après v1.3.2

---

## Idées évoquées sans décision formelle

⚠️ Ces éléments ont été mentionnés mais pas actés. **Ne pas implémenter sans confirmation.**

### WifiMapper

- Web app locale Python (Flask ou FastAPI)
- Heatmap Wi-Fi pour PME
- Hybride : simulation + mesures réelles (`nmcli dev wifi list` en boucle)
- Brainstorming réalisé en session 2026-06-03b — pas de spec formelle

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
| v1.3.0 | 2026-06-03 | TLS Inspector, SMB/NFS, Hosts File, install.sh |
| v1.3.1 | 2026-06-05 | SSH Key Manager, aide contextuelle (help_page.py) |
| v1.3.2 | 2026-06-06 | i18n 8 langues, aide contextuelle 8 langues × 27 modules |
| v1.3.5 | 2026-06-06 | Compatibilité macOS — 9 modules dual Linux/macOS |
