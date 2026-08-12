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

---

## DT-16 — Terminal SSH : sessions multiples en onglets (vs session unique)

**Contexte :** Signalé par l'utilisateur : reconnecter une connexion enregistrée (double-clic sur le même élément de l'arbre, ou une deuxième connexion pendant qu'une session tournait déjà) tuait la session active sans jamais rouvrir de terminal fonctionnel. Cause racine : `SshPage` ne portait qu'un seul `SshWorker`/`TerminalView` global (page `_TERMINAL` unique) — toute nouvelle connexion arrêtait d'abord l'ancienne session avant d'en démarrer une nouvelle sur le même widget. Un test isolé (cycle stop/start du `SshWorker` seul, hors GUI) a confirmé que le mécanisme bas niveau fonctionnait correctement ; le vrai problème était l'absence de support multi-session, pas un bug de threading.

**Décision :** Remplacer le widget terminal unique par un `QTabWidget` (`SshPage._term_tabs`). Chaque connexion — via double-clic, bouton « Se connecter » ou menu contextuel — ouvre systématiquement un **nouvel onglet** (`_SshSessionTab`), jamais un remplacement. Un onglet encapsule son propre `SshWorker` + `TerminalView` + en-tête (statut, nom, bouton Déconnecter). Fermer un onglet (bouton x) arrête son worker et le retire ; fermer la page (`closeEvent`) arrête tous les workers actifs.

**Raisons :**
- Usage réel attendu : plusieurs sessions simultanées, y compris vers le même hôte (ex. un terminal pour un `tail -f`, un autre pour l'administration).
- Isole l'échec/la fin d'une session (code de sortie, erreur réseau) des autres sessions ouvertes.
- Conserve `SshWorker`/`TerminalView` inchangés (`core/terminal.py`, `pages/terminal_view.py`) — seule `SshPage` change de structure.

**Alternatives rejetées :**
- Dédupliquer par connexion (un seul onglet par `conn.id`, réutilisé si déjà ouvert) : rejeté, empêche d'ouvrir deux sessions vers le même hôte, cas d'usage explicitement voulu.
- Fenêtres séparées par session (multi-fenêtrage Qt) : rejeté, plus lourd à intégrer avec la sidebar/l'arbre de connexions existants qu'un `QTabWidget` dans la page actuelle.

## DT-17 — Terminal SSH : taille PTY perdue si `resize()` arrive avant le spawn (SIGWINCH manqué)

**Contexte :** Signalé par l'utilisateur : dans une app plein écran côté distant (ex. Claude Code CLI, htop, vim), en arrivant en bas de l'écran l'affichage semblait « revenir en haut » sans effacer le texte du bas, qui ne se nettoyait que progressivement en continuant à taper/défiler. Redimensionner la fenêtre de l'app faisait disparaître le phénomène — indice déterminant.

Cause racine : `SshPage._start_session()` fait `addTab(...)` puis `tab.start()` de façon synchrone, sans laisser Qt traiter le layout de l'onglet fraîchement ajouté. `_SshSessionTab.start()` construit `SshWorker(build_ssh_args(conn))` **sans** passer `rows`/`cols` → il démarre avec les défauts du constructeur (24×80), qui matchent le `pyte.HistoryScreen(80, 24)` créé à l'`__init__` de `TerminalView`. Peu après, une fois que Qt traite le layout en attente, `TerminalView.resizeEvent` calcule la vraie taille du widget (souvent différente de 24×80) et émet `resize_pty`, câblé à `SshWorker.resize()`. Mais `worker.start()` (démarrage du `QThread`) est asynchrone : `ptyprocess.PtyProcess.spawn()` tourne sur le thread du worker et peut ne pas avoir encore assigné `self._proc` au moment où `resize()` s'exécute sur le thread principal. Ancien code : `resize()` ne faisait rien si `self._proc` était `None` — la taille demandée était silencieusement perdue, sans jamais être réappliquée. Résultat : le PTY reste bloqué à 24×80 côté noyau (`TIOCSWINSZ`) alors que `pyte`/`TerminalView` affichent la vraie taille (plus grande) — l'app distante calcule son défilement/repositionnement de curseur sur de mauvaises dimensions, d'où les résidus visuels. Redimensionner la fenêtre déclenche un nouveau `resizeEvent` → un nouveau `resize_pty.emit()` → cette fois `self._proc` existe → `setwinsize()` réussit → SIGWINCH livré → l'app distante se recale.

**Décision :** `SshWorker` mémorise la dernière taille demandée dans `self._pending_size`, y compris quand `self._proc` n'existe pas encore. Juste après `ptyprocess.PtyProcess.spawn()` dans `run()`, si `_pending_size` est défini, on applique `setwinsize()` immédiatement — aucune taille demandée avant le spawn n'est plus perdue.

**Raisons :**
- Corrige la cause racine (race condition) plutôt que de contourner par un délai/sleep arbitraire avant `worker.start()`.
- Reste localisé à `core/terminal.py`, aucun changement de `TerminalView`/`SshPage` nécessaire.

**Alternatives rejetées :**
- Retarder `tab.start()` après un `QTimer.singleShot(0, ...)` ou un `processEvents()` pour laisser le layout se faire avant de spawner : rejeté, ne garantit toujours pas que le thread worker ait fini `PtyProcess.spawn()` avant le premier `resizeEvent` (juste réduit la fenêtre de course sans l'éliminer).
- Passer `rows`/`cols` explicites à `SshWorker` depuis `_SshSessionTab.start()` : rejeté seul, la taille du widget au moment de `start()` n'est pas fiable (onglet tout juste ajouté, pas encore layouté) — n'aurait fait que déplacer le problème.

---

## DT-18 — Flatpak local (KDE Linux) : `flatpak-spawn --host` plutôt que sandboxer chaque outil

> **Dépassé (v1.7.12, voir DT-21) :** Le packaging Flatpak a été retiré du dépôt après découverte d'une limitation noyau bloquante pour le terminal SSH par mot de passe (`TIOCSCTTY` refusé — EPERM). Section gardée pour l'historique et pour quiconque reconsidérerait Flatpak plus tard : l'essentiel de l'approche (shim générique, `--filesystem=home`, choix du BaseApp PySide6) fonctionnait bien ; seule l'authentification SSH par mot de passe s'est révélée non résolvable proprement.

**Contexte :** Demande d'un manifest Flatpak local pour KDE Linux (distro immuable où Flatpak est le seul canal d'installation sérieux — contrairement à Arch/AUR ou NixOS/`flake.nix`, déjà couverts). nmlinux shelle vers ~30 binaires système (`nmcli`, `ip`, `pkexec`, `ssh`, `mount.cifs`, `nmap`, `xfreerdp`, `smbclient`, …) qui doivent agir sur le vrai NetworkManager, le vrai `/etc/hosts`, les vrais montages — pas de D-Bus direct depuis le code Python (`QtDBus` listé en hidden-import PyInstaller mais jamais utilisé).

**Décision :** Runtime `org.kde.Platform//6.11` + base `io.qt.PySide.BaseApp//6.11` (Flathub, `BASEAPP_REMOVE_WEBENGINE=1`/`BASEAPP_DISABLE_NUMPY=1` — nmlinux n'utilise ni l'un ni l'autre). `flatpak-pip-generator` refuse explicitement de générer un module pip pour PySide6 (« Please use the baseapp https://github.com/flathub/io.qt.PySide.BaseApp ») : PySide6 depuis PyPI est un wheel énorme qui embarque son propre Qt, alors que le BaseApp le compile contre le Qt du runtime KDE — c'est le chemin que l'écosystème Flathub a construit pour ce problème précis, pas la peine de le refaire à la main. Seuls `ptyprocess`, `pyte`, `tftpy` et `hatchling` (backend de build) passent par un module `python3-requirements` généré par ce même outil. Chaque binaire hôte appelé par nmlinux est shimmé via un script générique (`packaging/flatpak/host-bin/host-spawn`, symlinké sous chaque nom) qui fait `exec flatpak-spawn --host "$(basename "$0")" "$@"`, placé en tête du `PATH` de l'app (`--env=PATH=/app/bin/host-bin:...`). Le code Python de nmlinux n'a aucune conscience du sandbox.

Corollaire découvert en implémentant : un chemin de fichier passé à une commande relayée ainsi doit être visible depuis l'espace de noms de montage de l'**hôte** — le `/tmp` privé du sandbox ne l'est pas. Trois call sites construisaient des chemins invisibles côté hôte : `smb_mount.py` (fichier credentials temporaire + `_MOUNT_HELPER` sous `/app`), `file_transfer.py` (`tftp_helper.py` sous `/app`, mode root), `hosts.py` (fichier temporaire avant `pkexec cp` vers `/etc/hosts`). `nmlinux/core/flatpak_shim.py` redirige ces trois cas vers `$XDG_CACHE_HOME/nmlinux/tmp` — le seul répertoire que Flatpak fait pointer vers un vrai chemin hôte (`~/.var/app/<id>/cache`) — no-op hors Flatpak (`FLATPAK_ID` absent de l'environnement).

**Raisons :**
- Sandboxer individuellement chaque outil d'administration système (montage SMB, polkit, scan raw socket) demanderait des permissions si larges (`--device=all`, `--filesystem=host`, D-Bus system par service) qu'elles videraient le sandbox de son sens — ces outils sont par nature hors du modèle de menace que Flatpak sandbox.
- `flatpak-spawn --host` est le pattern déjà utilisé par des apps d'administration/dev connues (GNOME Builder, VS Code Flatpak) pour ce même besoin.
- Aucune réécriture des ~30 call sites `subprocess.run(["nmcli", ...])` existants : la résolution `PATH` fait tout le travail.
- `--filesystem=home` reste volontairement large pour ce premier passage (pas de portail `FileChooser` ciblé) — acceptable pour un manifest local non soumis à Flathub, à resserrer si publication un jour envisagée.

**Alternatives rejetées :**
- `org.freedesktop.Platform` + PySide6 installé via `flatpak-pip-generator` : tenté en premier, rejeté — l'outil lui-même refuse ce cas (wheel PySide6 non géré) et redirige vers le BaseApp ; l'aurait-il accepté que ça aurait dupliqué Qt (une copie dans le runtime freedesktop minimal — en fait absente — et une dans le wheel) pour un résultat plus fragile que le BaseApp maintenu par Flathub.
- Réécrire chaque call site pour préfixer `flatpak-spawn --host` explicitement dans le code Python : rejeté, couplerait ~30 fichiers au fait de tourner ou non sous Flatpak alors que le shim PATH résout ça avec zéro changement de logique métier.
- Bundler les outils système eux-mêmes dans le Flatpak (nmap, mtr, cifs-utils…) : rejeté, dupliquerait des paquets déjà présents sur l'hôte et cassé pour tout ce qui doit agir sur l'état réel de l'hôte (montages, `/etc/hosts`, NetworkManager) plutôt que dans un espace de noms isolé.

## DT-19 — Traceroute : `shutil.which()` ment sous Flatpak, fallback sur l'échec plutôt que sur l'absence

**Contexte :** Sous le Flatpak local (DT-18), `packaging/flatpak/host-bin/` contient un symlink pour **chaque** nom de binaire relayé — y compris `traceroute`, qui n'est qu'une dépendance optionnelle côté hôte (seul `tracepath`/`iputils`, requis, est garanti présent — voir CLAUDE.md §7). `TracerouteWorker` choisissait `traceroute` vs `tracepath` via `shutil.which('traceroute')` : dans le sandbox ce test renvoie toujours un chemin (le shim existe toujours), même quand l'hôte n'a pas le vrai binaire. Le shim fait alors `flatpak-spawn --host traceroute …`, qui échoue côté hôte en imprimant une ligne d'erreur qui ne matche aucune regex de hop/star — le worker termine donc instantanément sans le moindre hop ni message d'erreur visible (`_proc.wait()` réussit, aucune exception Python n'est levée).

**Décision :** `_run_traceroute()` retourne désormais `True`/`False` selon qu'au moins un hop ou un `*` a été trouvé (`bool(seen)`). Si `False` (et que l'utilisateur n'a pas cliqué Stop entre-temps — `self._stopped`), `run()` retente automatiquement avec `tracepath`. `finished` n'est émis qu'une seule fois, à la fin de `run()`, plutôt que dans un `finally` de chaque méthode `_run_*`.

**Raisons :**
- Corrige le fallback à la source : `shutil.which()` teste la présence du *nom* dans le `PATH` du process, pas la capacité réelle du binaire final à s'exécuter — invalide dès qu'un shim générique est interposé.
- Détecter l'échec par « zéro sortie exploitable » plutôt que par code de retour : `flatpak-spawn --host` sur un binaire absent ne lève pas d'exception Python, et le code de sortie du process traceroute lui-même n'est pas fiable à travers le relais (peut être celui de `flatpak-spawn`, pas celui de la commande spawnée).
- Le flag `_stopped` évite qu'un arrêt manuel avant le premier hop soit interprété comme un échec de `traceroute` et relance silencieusement un `tracepath` non désiré.

**Alternatives rejetées :**
- Sonder l'hôte au démarrage de l'app (`flatpak-spawn --host which traceroute`) pour fixer `_CMD_TRACEROUTE` correctement une fois pour toutes : rejeté, ajoute un aller-retour flatpak-spawn synchrone au démarrage pour un cas qui ne se manifeste qu'à l'usage du module Traceroute, alors que le fallback par échec le résout sans coût au chargement.
- Faire lister par le manifeste Flatpak uniquement les shims des outils garantis présents (retirer `traceroute` de `host-bin/`) : rejeté, `traceroute` reste utile quand l'hôte l'a réellement installé (sortie plus riche que `tracepath` — RTT par sonde, pas de limite de 30 hops arbitraire) ; le retirer supprimerait ce cas plutôt que le gérer.

## DT-20 — Terminal SSH : mot de passe jamais demandé sous Flatpak (`flatpak-spawn` ne relaie pas l'environnement)

> **Dépassé (v1.7.12, voir DT-21) :** `packaging/flatpak/host-bin/` n'existe plus dans le dépôt — le Flatpak a été retiré, ce correctif de shim avec lui. Section gardée pour l'historique : le piège « `flatpak-spawn --host` ne relaie pas l'environnement » reste vrai et utile si un shim similaire est réintroduit un jour. Le seul survivant côté code est `SSH_ASKPASS_REQUIRE=never` dans `nmlinux/core/terminal.py`, gardé comme garde-fou défensif hors Flatpak (sans effet mesurable, sans risque).

**Contexte :** Sous le Flatpak local, une connexion SSH par mot de passe échouait systématiquement (`Permission denied, please try again.` × 3 puis `Permission denied (publickey,password)`) sans jamais afficher de prompt `password:` dans le terminal intégré. Le vrai `ssh` (`packaging/flatpak/host-bin/ssh` → `flatpak-spawn --host ssh …`) tentait `$SSH_ASKPASS` (`ssh_askpass: exec(/usr/lib/ssh/ssh-askpass): No such file or directory`) au lieu de demander le mot de passe sur le pty — openssh bascule sur askpass quand `DISPLAY`/`WAYLAND_DISPLAY` sont présents dans l'environnement du process. Premier correctif tenté (rejeté, voir plus bas) : poser `SSH_ASKPASS_REQUIRE=never` dans l'environnement Python du `subprocess`/`ptyprocess` qui spawn le shim — sans effet en pratique sous Flatpak. Cause : `flatpak-spawn --host` ne transmet **pas** l'environnement du process appelant (sandboxé) vers le process hôte — seul `--env=VAR=VALUE` explicite le fait (confirmé via `flatpak-spawn --help` depuis le sandbox). Le `ssh` réel côté hôte hérite donc de l'environnement de la session hôte elle-même (qui a un vrai `DISPLAY`/`WAYLAND_DISPLAY`, session graphique oblige), jamais de ce que nmlinux pose côté sandbox — d'où l'échec silencieux du fix initial.

**Décision :** Le shim générique `packaging/flatpak/host-bin/host-spawn` ajoute `--env=SSH_ASKPASS_REQUIRE=never` à l'appel `flatpak-spawn --host` pour **toutes** les commandes relayées (pas seulement `ssh`). `nmlinux/core/terminal.py` garde en plus `SSH_ASKPASS_REQUIRE=never` dans l'environnement du `subprocess` (utile hors Flatpak, où `ssh` est spawné directement — sans effet mais sans risque sous Flatpak).

**Raisons :**
- Le fix doit vivre au niveau du relais (`flatpak-spawn --host --env=...`), pas dans le code Python de nmlinux, qui n'a — et ne doit pas avoir, DT-18 — conscience du sandbox.
- Appliquer `--env=SSH_ASKPASS_REQUIRE=never` à toutes les commandes plutôt que juste `ssh` : plus simple qu'un `case "$(basename "$0")" in ssh|sshpass) ... ;; esac` dans le shim, et la variable est inoffensive pour `nmcli`/`ip`/`mount.cifs`/etc. qui l'ignorent.
- Piège à retenir pour tout futur besoin de forwarder une variable d'env vers l'hôte via ce shim : `flatpak-spawn --host` n'en transmet aucune par défaut, contrairement à l'intuition (« c'est juste un exec distant »).

**Alternatives rejetées :**
- Fixer côté Python (`terminal.py` seul, tentative initiale) : ne fonctionne pas sous Flatpak — `flatpak-spawn --host` ignore l'environnement du process appelant.
- `--env-fd` ou `--clear-env` sur le shim pour repartir d'un environnement hôte propre : rejeté, `--clear-env` supprimerait aussi des variables utiles côté hôte (`PATH` réel, locale, etc.) pour un gain nul ici — un seul `--env=` ciblé suffit.

## DT-21 — Flatpak retiré du dépôt : `TIOCSCTTY` refusé (EPERM) par le noyau, pas contournable proprement

**Contexte :** Après DT-20, le message d'erreur `ssh_askpass` avait disparu mais la connexion SSH par mot de passe échouait toujours — 3 tentatives « Permission denied, please try again. » sans jamais laisser l'utilisateur taper quoi que ce soit. Diagnostic (reproduit hors sandbox avec `ptyprocess.PtyProcess.spawn(['flatpak', 'run', '--command=sh', ...])`, un vrai pty de bout en bout) : `flatpak-spawn --host tty` renvoie bien un device réel (`/dev/pts/N` — le fd forwardé EST un vrai pty), mais `flatpak-spawn --host cat /dev/tty` échoue avec `No such device or address` (ENXIO) — le process hôte n'a **aucun terminal contrôlant**, alors qu'OpenSSH (`read_passphrase()`) ouvre `/dev/tty` explicitement pour les prompts interactifs, pas juste `stdin`.

Tentative de réparation avec `setsid -c` (établir le fd forwardé comme ctty) : échec avec `Operation not permitted`. Cause identifiée : ce pty a été créé par un processus dans une **session complètement différente** (celle qui a appelé `ptyprocess.spawn`, jamais un ancêtre du process spawné côté hôte par le portail xdg-desktop-portal — les deux arbres de processus ne partagent que des fd dupliqués via le passage de fd D-Bus du `Spawn` du portail). Le noyau refuse explicitement qu'un process d'une session tierce s'approprie le terminal contrôlant d'une session à laquelle il n'appartient pas, sans `CAP_SYS_ADMIN` — restriction de sécurité intentionnelle, pas un bug de `flatpak-spawn`.

Seul contournement testé et fonctionnel : `script -qec "ssh …" /dev/null`, qui alloue un **nouveau** pty possédé par sa propre session (donc `TIOCSCTTY` y réussit légitimement). Confirmé par test direct (écriture de bytes via le pty d'origine, lus et ré-échoués par `cat /dev/tty` à travers `script`). Mais un redimensionnement de fenêtre appliqué au pty d'origine (`ptyprocess.setwinsize()`, ce que fait `SshWorker.resize()`, DT-17) ne se propage **jamais** au pty interne de `script` — testé (`stty size` avant/après `setwinsize(40, 120)` : toujours `24 80`) — pour la même raison structurelle : ni `script` ni quoi que ce soit d'autre côté hôte n'est jamais propriétaire de session du pty d'origine, donc ne reçoit jamais `SIGWINCH` pour lui ; seul un correctif supplémentaire (relais actif par polling `TIOCGWINSZ`→`TIOCSWINSZ`, ~300 ms, écrit spécifiquement pour ce cas) aurait pu combler ce trou.

**Décision :** Abandon complet du packaging Flatpak plutôt que de livrer ce contournement. `packaging/flatpak/` retiré du dépôt, remote Flatpak local désinstallé. AUR et AppImage redeviennent les seuls canaux d'installation Linux.

**Raisons :**
- Le terminal SSH intégré (sessions multiples, copier/coller, resize — DT-14/16/17) est une fonctionnalité centrale de nmlinux ; livrer un packaging où l'authentification par mot de passe est purement et simplement cassée (aucun contournement disponible pour l'utilisateur, pas juste dégradée) n'est pas acceptable pour un canal de distribution annoncé comme fonctionnel.
- Le contournement `script` répare le mot de passe mais réintroduit une régression sur une fonctionnalité déjà corrigée avec effort (DT-17) — écrire et maintenir un relais de resize par polling pour un cas d'usage aussi étroit (SSH par mot de passe, spécifiquement sous Flatpak) n'était pas jugé proportionné.
- Contrairement aux bugs DT-19/DT-20 (corrigibles proprement côté application), celui-ci est une limitation d'isolation noyau — pas quelque chose que nmlinux ou même le manifeste Flatpak peuvent résoudre sans compromis structurel.
- AUR et AppImage n'ont aucun de ces problèmes : `ssh` y tourne directement, sans relais, sans conflit de session.

**Alternatives rejetées :**
- Livrer `script`-wrapping quand même, en acceptant la régression de resize : rejeté — remplacerait un bug bloquant (mot de passe) par un autre, plus subtil (resize silencieusement cassé uniquement pour les sessions par mot de passe sous Flatpak), difficile à diagnostiquer pour un futur mainteneur sans ce contexte.
- Écrire un relais de resize par polling dédié pour accompagner `script` : rejeté pour l'instant — complexité et surface de maintenance disproportionnées pour un cas d'usage étroit (Flatpak + auth par mot de passe uniquement), réévaluable si Flatpak est un jour redemandé.
- Askpass GUI personnalisé bundlé (popup Qt ou appel à `kdialog --password`/`zenity --password` côté hôte, avec `SSH_ASKPASS_REQUIRE=force`) : non retenu pour cette itération — aurait sans doute fonctionné (les popups GUI traversent `flatpak-spawn --host` sans le problème de ctty), mais change l'UX (popup externe au lieu d'un prompt inline dans le terminal intégré) et ajoute une dépendance hôte optionnelle (`kdialog`/`zenity`) non garantie sur toutes les cibles Flatpak ; à reconsidérer si Flatpak revient au planning.
