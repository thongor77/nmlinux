# CLAUDE.md — Point d'entrée agent

Ce fichier est le point d'entrée unique pour tout agent Claude travaillant sur ce dépôt.
**Lire entièrement avant toute action.**

---

## 1 — Base de connaissances

```
docs/
├── Architecture.md        — structure du code, patterns, dépendances
├── Carte-des-Modules.md   — 27 modules : backend, worker, persistence, export
├── Decisions-Techniques.md— pourquoi le code est comme il est (DT-01 à DT-13)
├── Roadmap.md             — fonctionnalités livrées et candidates
├── Maintenance-IA.md      — recettes : nouveau module, i18n, injection, release
└── Journal.md             — jalons techniques par version
```

### Quel document consulter selon la tâche

| Type de tâche | Documents à lire |
|---------------|-----------------|
| Ajouter un module | Architecture.md + Carte-des-Modules.md + Maintenance-IA.md |
| Modifier i18n / help_content | Architecture.md §i18n + Maintenance-IA.md |
| Corriger un bug UI (thème, layout) | Architecture.md §thème + Decisions-Techniques.md DT-02, DT-11 |
| Faire une release | Maintenance-IA.md §Release + Roadmap.md |
| Comprendre une décision existante | Decisions-Techniques.md |
| Ajouter une persistence JSON | Architecture.md §Persistence + Carte-des-Modules.md |
| Première prise en main | Architecture.md en entier |

---

## 2 — Règles de documentation

**La documentation fait partie du livrable. Une tâche est incomplète si les docs ne sont pas à jour.**

### Mettre à jour `docs/Carte-des-Modules.md` quand

- Un nouveau module est ajouté (ajouter une section complète).
- Un module change de backend, de persistence ou d'options d'export.
- Un module est supprimé.

### Enregistrer une décision dans `docs/Decisions-Techniques.md` quand

- Un choix technique non-évident est fait (technologie, architecture, format).
- Une alternative a été explicitement rejetée.
- Un piège ou un bug subtil a été découvert et corrigé (ex : DT-13 injection i18n).
- La règle : si quelqu'un pourrait se demander "pourquoi c'est fait comme ça ?", c'est une DT.

Format obligatoire :
```
## DT-NN — Titre court

**Contexte :** situation avant la décision.
**Décision :** ce qui a été choisi.
**Raisons :** pourquoi (liste).
**Alternatives rejetées :** ce qui n'a pas été retenu et pourquoi.
```

### Mettre à jour `docs/Roadmap.md` quand

- Une version est livrée (ajouter une ligne dans le tableau des versions).
- Une nouvelle fonctionnalité est confirmée par l'utilisateur (ajouter sous "Candidats vérifiés").
- Une idée est évoquée sans décision (ajouter sous "Idées évoquées sans décision formelle").
- Une fonctionnalité candidate est implémentée (la retirer des candidats, l'ajouter au tableau).

### Mettre à jour `docs/Journal.md` quand

- Une version est livrée (ajouter un jalon).
- Une décision architecturale majeure est prise (référencer la DT correspondante).

### Mettre à jour ce fichier (`CLAUDE.md`) quand

- Le nombre de langues i18n change.
- Le nombre de tests change significativement.
- Un nouveau fichier de persistence est ajouté.
- Une recette de workflow change (release, AUR, injection).

---

## 3 — Lancement et build

```bash
# Développement
python3 -m nmlinux.main    # ou ./nmlinux.sh

# Installé
nmlinux

# Build wheel (le sdist échoue — symlink dans aur/)
python -m build --wheel --no-isolation

# Tests (37 tests, logique pure, pas de Qt)
pytest tests/ -v
```

---

## 4 — Architecture (résumé)

Détails complets dans `docs/Architecture.md`.

`window.py` — `MainWindow` : `QListWidget` sidebar + `QStackedWidget`. Chaque page est enregistrée dans `_TOOLS` comme `(icon_names, label, PageClass, tooltip)`. Ajouter une page = append à `_TOOLS` + import + clés i18n + contenu help.

`nmlinux/core/` — utilitaires partagés :
- `i18n.py` — `tr(key, **kwargs)` : 8 langues (fr/en/es/de/it/pt/ja/zh), ~720 clés chacune. `fr` est la référence (toujours complète). Ajouter dans les **8 blocs**.
- `theme.py` — `is_dark()`, `color_ok()`, `color_err()` : appeler à la création des widgets, jamais au chargement du module. Surcharger `changeEvent(ApplicationPaletteChange)` + `update()` sur les widgets avec dessin custom.
- `cli_bar.py` — `get_cli_bar().set_cmd(cmd)` : dans `_update_cli()`, branché sur `showEvent` et les changements de paramètres.
- `settings.py` — singleton `AppSettings`. Accès via `.language`, **pas** `.get()`.
- `help_content.py` — `get_help(label)` : aide contextuelle 8 langues × 27 modules.
- `icons.py` — `themed_icon(*names)` : 21 SVG Lucide bundlés, couleur `#60a5fa`, aucun thème système requis.

Pattern page standard :

```python
class FooPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        # addWidget(table, 10) + addStretch(1) — évite le centrage Qt

    def showEvent(self, event) -> None:
        self._update_cli()
        super().showEvent(event)
```

Tout travail bloquant → `QThread` avec `Signal`s typés. Constantes de colonnes au niveau module : `_C_IP, _C_HOST = range(2)`.

---

## 5 — i18n — vérification rapide

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from nmlinux.core import i18n
fr = set(i18n._T['fr'].keys())
for lang in ['en','es','de','it','pt','ja','zh']:
    m = fr - set(i18n._T.get(lang,{}).keys())
    if m: print(f'{lang}: {sorted(m)}')
"
```

---

## 6 — Injection programmatique dans help_content.py

⚠️ Piège documenté — voir `docs/Decisions-Techniques.md` DT-13.

```python
# CORRECT
result += "        },"   # PT_CLOSE — ferme le dernier bloc langue existant
result += NEW_BLOCK      # nouveau bloc (\n        "xx": {...},)
result += "\n    },"     # MOD_CLOSE — ferme le module

# FAUX : result += NEW_BLOCK + PATTERN
# → le nouveau bloc s'imbrique dans le dernier bloc (syntaxe Python valide, sémantique incorrecte)
```

---

## 7 — Dépendances système

Obligatoires : `networkmanager` (nmcli), `iproute2` (ip), `iputils` (ping/tracepath)

Optionnelles : `nmap`, `whois`, `net-snmp`, `bind` (dig), `traceroute`, `python-hwdata`,
`nm-connection-editor`, `samba` (smbclient), `nfs-utils` (showmount), `openssl`,
`xfreerdp`/`xfreerdp3`, `vncviewer` (TigerVNC), `mtr`, `curl`, `wakeonlan`,
`openssh` (ssh-keygen), `pkexec` (polkit)

---

## 8 — Release

Procédure complète dans `docs/Maintenance-IA.md` §Release. Résumé :

```bash
# 1. Bumper nmlinux/__init__.py + pyproject.toml + README.md
# 2. git commit + git tag -a vX.Y.Z + git push --tags
# 3. python -m build --wheel --no-isolation
# 4. gh release create vX.Y.Z dist/nmlinux-X.Y.Z-py3-none-any.whl ...
# 5. Mettre à jour aur/PKGBUILD (pkgver + sha256) + .SRCINFO + push AUR
```

AUR : compte `magetriste`, clé `~/.ssh/id_aur`. GitHub : compte `thongor77`.

---

## 9 — Persistence

| Fichier | Contenu |
|---------|---------|
| `~/.local/share/nmlinux/settings.json` | Langue (`AppSettings`) |
| `~/.local/share/nmlinux/ssh_connections.json` | Connexions SSH (format v2) |
| `~/.local/share/nmlinux/rdp_connections.json` | Connexions RDP (format v2) |
| `~/.local/share/nmlinux/vnc_connections.json` | Connexions VNC (format v2) |
| `~/.local/share/nmlinux/wol_hosts.json` | Hôtes Wake on LAN |
| `~/.local/share/nmlinux/speedtest_history.json` | 5 derniers tests de débit |
| `~/.local/share/applications/nmlinux.desktop` | Entrée menu application |
