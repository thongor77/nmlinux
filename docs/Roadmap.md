# Roadmap NMLinux

## Version courante : v1.3.5 (2026-06-06)

27 modules, 8 langues UI, aide contextuelle 8 langues × 27 modules, compatibilité macOS.

---

## Candidats vérifiés (mentionnés explicitement par l'utilisateur)

Ces idées ont été discutées et validées — elles ne sont pas encore implémentées.

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
