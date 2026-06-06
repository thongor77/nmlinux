# Décisions Techniques

Chaque décision est documentée avec son contexte, le choix retenu et les alternatives rejetées.

---

## DT-01 — Python/PySide6 plutôt que .NET/Avalonia

**Contexte :** Le projet original (NETworkManager by BornToBeRoot) est en C#/WPF, Windows uniquement. Un portage .NET/Avalonia avait été commencé (branche `NetworkManager`).

**Décision :** Abandon du portage .NET/Avalonia. Réécriture complète en Python 3.11 + PySide6 (Qt 6).

**Raisons :**
- Avalonia sur Linux avec GPU NVIDIA/AMD Wayland produisait des artefacts de rendu bloquants.
- Qt est le framework natif KDE ; PySide6 s'intègre naturellement au thème système (Breeze).
- Python permet d'itérer rapidement sur 27 modules sans compilateur.
- Pas de dépendance à un runtime .NET supplémentaire pour l'utilisateur Linux.

**Retour de BornToBeRoot (mai 2026) :** "Cross-platform is on my roadmap for NETworkManager, but WPF being Windows-only is the main blocker. The heavy part is porting the entire UI to something like Avalonia — quite a lot of work, even with AI assistance." → Confirmation que nmlinux reste indépendant.

---

## DT-02 — Terminal SSH : pyte + QPainter (vs QPlainTextEdit + strip_ansi)

**Contexte :** La v1 utilisait `QPlainTextEdit` avec un strip ANSI manuel et des sentinelles Unicode pour les séquences de contrôle.

**Problème :** Architecture fondamentalement incompatible avec ZSH Line Editor (ZLE). Chaque correctif exposait un nouveau cas limite (curseur dupliqué, `clear` trop agressif, flèche haut efface le prompt, prompt multiplié au resize). 7 commits de correctifs successifs.

**Décision :** Migration complète vers `pyte.HistoryScreen` + `QPainter` (commit `85ba878`).

**Architecture retenue :**
- `SshWorker` émet les bytes PTY bruts (`Signal(bytes)`) sans aucun traitement.
- `TerminalView.feed(bytes)` les injecte dans `pyte.HistoryScreen(2000)`.
- `paintEvent` lit `screen.buffer` case par case et dessine avec `QPainter`.

**Avantages :** pyte gère tout VT100/VT220/xterm en interne. Scrollback (2000 lignes) via `pyte.HistoryScreen`. Support 256 couleurs et truecolor. Curseur clignotant. Palette Catppuccin Mocha fixe (terminal intentionnellement non soumis au thème Qt).

---

## DT-03 — Icônes bundlées Lucide (vs QIcon.fromTheme)

**Contexte :** v1.2.6 — icônes cassées sur GNOME/Adwaita et NixOS/KDE car `QIcon.fromTheme()` dépend du thème système.

**Problème :** Sur NixOS, Breeze 6.x livre uniquement des SVGZ ; le plugin `libqsvg.so` est dans `qt6.qtsvg`, un package Nix séparé. Sur GNOME, aucun thème KDE disponible.

**Décision :** 21 SVG Lucide (MIT) bundlés dans `assets/icons/`. Rendu runtime via `QSvgRenderer + QPainter` à 22 px. Couleur unique `#60a5fa` (bleu). Cache `@lru_cache(maxsize=64)`.

**Interface publique inchangée :** `themed_icon(*names)` continue de fonctionner avec les noms hérités grâce à `_NAME_MAP`.

**Conséquence :** L'app ne dépend plus d'aucun thème système.

---

## DT-04 — PTY local pour le terminal SSH (vs externe)

**Décision :** `SshWorker` utilise `ptyprocess.PtyProcess.spawn(["ssh", ...])` — ssh tourne dans un PTY embarqué dans l'application, pas dans un terminal externe.

**Raison :** L'embedding était une exigence explicite du projet (voir `feedback_pyside6_patterns.md` en mémoire Claude). Un simple `subprocess.Popen` + terminal externe (`konsole -e ssh ...`) existe aussi dans `core/ssh.py` comme fallback mais n'est pas utilisé dans la page SSH principale.

**Contraintes résolues :**
- `TERM=xterm-256color` forcé via `_env.setdefault()` (ZSH bascule en mode dégradé sans TERM).
- Echo PTY désactivé via `termios.tcsetattr()` après spawn (SSH réinitialise ECHO pendant le handshake).
- `_kill_echo()` appelé 8 fois en début de session pour contrer le reset SSH.

---

## DT-05 — Pas de root requis (sauf exceptions documentées)

**Décision :** Toutes les fonctionnalités s'exécutent sans `sudo`, sauf :
- `nmap -sS` / `-O` / `-A` (SYN scan et OS detection) — nécessitent root.
- Lecture live du ruleset firewall (`nft list ruleset`) — via `pkexec`.
- Sauvegarde de `/etc/hosts` — via `pkexec cp` (authentication polkit).

**Raison :** Minimiser la surface d'attaque et la friction utilisateur.

---

## DT-06 — Modèle de données SSH/RDP/VNC : groupes + connexions séparés

**Décision :** Les profils de connexion (SSH, RDP, VNC) utilisent deux listes séparées : `groups` (arborescence) et `connections` (profils). Chaque entité a un UUID. `Connection.group_id = ""` → racine.

**Format JSON v2 :**
```json
{
  "version": 2,
  "groups": [{"id": "...", "name": "...", "parent_id": ""}],
  "connections": [{"id": "...", "group_id": "...", ...}]
}
```

**Rétrocompatibilité v1 :** `SshStore.load()` détecte le format liste plate et le migre silencieusement. RDP et VNC ont été créés directement en v2.

**Profondeur :** Récursive illimitée (sous-groupes de sous-groupes).

---

## DT-07 — Mots de passe : jamais stockés

**Décision :** Les mots de passe SSH, RDP et VNC ne sont **jamais** persistés. RDP et VNC demandent le mot de passe à la connexion via un `QInputDialog`. SSH délègue à l'agent SSH ou à la passphrase de clé.

---

## DT-08 — Speed Test via curl + Cloudflare (vs speedtest-cli)

**Contexte :** `speedtest-cli` (Ookla) renvoyait des erreurs de serveurs injoignables lors des tests.

**Décision :** Backend `curl` + `speed.cloudflare.com` :
- Download : `curl https://speed.cloudflare.com/__down?bytes=25000000`
- Upload : `curl -T /dev/zero https://speed.cloudflare.com/__up` (limité à ~10 MB)
- Ping : `ping -c 10 1.1.1.1`

**Avantage :** Pas de dépendance Python supplémentaire. `curl` est universel sur Linux.

---

## DT-09 — Firewall : lecture sans root, live avec pkexec

**Décision :** Sources lues sans root : `/etc/nftables.conf`, `/etc/iptables/iptables.rules`, `/etc/iptables/ip6tables.rules`. Le ruleset live nécessite `pkexec nft list ruleset` (polkit).

**Parsers :** `parse_nft()` et `parse_iptables()` séparés. Extraction des ports via `_ports_nft()` / `_ports_iptables()`. Colonnes : Table / Chain / Rule / Port / Action / Comment.

---

## DT-10 — Traceroute : géolocalisation par hop (vs batch en fin)

**Décision :** `GeolocWorker` appelle `ip-api.com/batch` **immédiatement à chaque hop découvert**, pas une seule fois en fin de traceroute.

**Raison :** L'utilisateur voit les points apparaître sur la carte en temps réel pendant que traceroute tourne.

**Contrainte :** IPs privées RFC-1918 skippées (pas de géoloc).

---

## DT-11 — Comportement du thème : palette Qt au runtime

**Décision :** Les widgets avec dessin custom doivent lire la palette Qt **à chaque `paintEvent`**, jamais à l'import du module. Implémenter `changeEvent(ApplicationPaletteChange)` + `update()` pour réagir aux changements de thème à chaud.

**Exception :** Le terminal (`TerminalView`) utilise une palette Catppuccin Mocha **fixe** — un terminal a intentionnellement ses propres couleurs, indépendantes du thème système.

---

## DT-12 — i18n : fallback fr, pas de fichiers .po

**Décision :** Toutes les traductions sont dans `core/i18n.py` comme un dict Python `_T`. Pas de fichiers `.po` / `.mo` / `gettext`.

**Raison :** Simplicité. Le volume de clés (~720 × 8 langues) reste gérable dans un seul fichier. Pas de dépendance à `babel` ou `gettext`.

**Fallback :** Si une clé manque dans la langue cible, `tr()` retourne la valeur `fr`. Le `fr` est la langue de référence (toujours complète).

---

## DT-13 — Injection i18n par script Python (vs réécriture manuelle)

**Contexte :** Ajout de 4 nouvelles langues (it/pt/ja/zh) dans `help_content.py` (~2700 lignes).

**Décision :** Injection programmatique : split du fichier sur le pattern `        },\n    },` (fermeture du module), insertion du nouveau bloc, reconstruction.

**Piège documenté :** Le pattern `        },\n    },` inclut le `},` de fermeture du dernier bloc existant. Insérer naïvement le nouveau bloc + PATTERN place le nouveau bloc **dans** le dernier bloc (imbrication silencieuse, syntaxe Python valide mais sémantique incorrecte).

**Bonne technique :**
```python
result += "        },"   # PT_CLOSE — ferme explicitement le dernier bloc existant
result += NEW_BLOCK      # nouveau bloc (commence par \n        "xx": {)
result += "\n    },"     # MOD_CLOSE — ferme le module
```
