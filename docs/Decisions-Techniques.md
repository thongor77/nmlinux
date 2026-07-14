# Décisions Techniques

Chaque décision est documentée avec son contexte, le choix retenu et les alternatives rejetées.

---

## DT-01 — Python/PySide6 plutôt que .NET/Avalonia

**Contexte :** Le projet original (NETworkManager by BornToBeRoot) est en C#/WPF, Windows uniquement. Un portage .NET/Avalonia avait été commencé (branche `NetworkManager`).

**Décision :** Abandon du portage .NET/Avalonia. Réécriture complète en Python 3.11 + PySide6 (Qt 6).

**Raisons :**
- Avalonia sur Linux avec GPU NVIDIA/AMD Wayland produisait des artefacts de rendu bloquants.
- Qt est le framework natif KDE ; PySide6 s'intègre naturellement au thème système (Breeze).
- Python permet d'itérer rapidement sur 29 modules sans compilateur.
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
- Echo PTY laissé activé (`echo=True`) — voir DT-14 : c'est ssh qui gère les modes du terminal.

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

---

## DT-14 — Terminal SSH : laisser ssh gérer l'écho (echo=True)

**Contexte :** Sur une VM Ubuntu 26.04 fraîche, après authentification le prompt s'affichait mais les frappes n'étaient plus jamais ré-affichées (clavier « mort »). Le debug `NMLINUX_DEBUG=1` montrait des lignes `WRITE` (octets bien envoyés au PTY) mais aucune `READ` en retour. Depuis une vraie console ssh, aucun problème.

**Cause :** `SshWorker` forçait l'écho **off** sur le PTY local (`ptyprocess.spawn(echo=False)` + `_kill_echo()` appelé sur les 8 premiers reads). Or le protocole SSH transmet les **modes du terminal local** au pty distant lors du `pty-req`. Avec l'écho local désactivé, ssh demandait au serveur « pas d'écho » → le shell distant n'écho plus rien. OpenSSH récent (Ubuntu 26.04) applique fidèlement ces modes ; les serveurs plus anciens les ignoraient parfois, ce qui masquait le bug.

**Décision :** Spawn avec `echo=True` (comme un vrai émulateur de terminal). On laisse ssh gérer les modes : il propage écho-on au pty distant **et** bascule le côté local en raw mode pour la session, donc pas de double-écho.

**Raisons :**
- L'écho de session est un écho **distant**, pas local. Le couper localement le coupe à la source.
- nmlinux n'écho jamais les frappes localement (`keyPressEvent` écrit seulement vers le PTY, ne nourrit pas pyte) → aucun risque de double-écho côté client.
- `_kill_echo()` corrigeait un problème inexistant : le « reset ECHO pendant le handshake » par ssh **était** la mise en place correcte de l'écho.

**Alternatives rejetées :**
- Garder `echo=False` et forcer l'écho distant autrement : impossible proprement, le seul canal côté client est justement les modes propagés par le `pty-req`.
- L'ancien `_kill_echo()` visait un faux « double-écho » : le bug de caractères dupliqués (commit `5fe69b8`) venait des redraws ZLE de ZSH dans l'ancien renderer QPlainTextEdit, pas de termios. Avec pyte il n'existe plus.

---

## DT-15 — iperf3 : client uniquement, onglet Speed Test (pas un module)

**Contexte :** Feature request GitHub issue #6 (`loren2018tw`) demandant le support d'iperf3 pour mesurer le débit LAN, complémentaire au Speed Test internet existant (DT-08). Cas d'usage confirmés : serveur fixe interne à une organisation, liste de serveurs publics par pays, comparaison IPv4/IPv6.

**Décision :**
- **Client seulement** (`iperf3 -c ... -J`) — pas de mode serveur (nmlinux n'écoute jamais en `iperf3 -s`).
- **Second onglet dans le module Speed Test existant** (`Internet` / `LAN`), pas un nouveau module dans la sidebar.
- Deux sources de serveur : liste publique bundlée en lecture seule (`assets/iperf3_public_servers.json`, 26 pays, sourcée depuis `R0GGER/public-iperf3-servers`) et serveurs personnalisés sauvegardés (`~/.local/share/nmlinux/iperf3_servers.json`, même pattern dataclass que `PingTarget`).

**Raisons :**
- iperf3 mesure un débit LAN point-à-point (nécessite une cible qui écoute), fondamentalement différent du test internet actuel (curl vers Cloudflare) — mais reste un « test de débit », donc un onglet du même module plutôt qu'un concept séparé dans la sidebar.
- Faire écouter nmlinux en permanence (mode serveur) change la surface sécurité/pare-feu de l'app d'une façon que le mode client ne fait pas — mérite sa propre spec si un besoin concret émerge, pas une extension improvisée du scope initial.
- La demande explicite ("liste par pays", "IPv4 vs IPv6") vient directement du auteur de la feature request — pas un choix arbitraire.

**Alternatives rejetées :**
- Nouveau module `IperfPage` dans la sidebar : rejeté, aurait dupliqué toute la logique de cartes/worker/CLI bar déjà présente dans Speed Test pour un concept très proche.
- Implémenter le mode serveur dès la v1 : reporté, pas de demande concrète au-delà de la suggestion initiale, complexité (pare-feu, port persistant) disproportionnée sans cas d'usage validé.
