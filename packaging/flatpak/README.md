# Flatpak — build local (KDE Linux)

Manifest local, non publié sur Flathub. Cible : KDE Linux (immuable) et
tout système où Flatpak est le seul canal d'installation sérieux — l'AUR
couvre Arch, `flake.nix` couvre NixOS (voir racine du dépôt).

## Pourquoi ce manifest est différent d'un Flatpak classique

nmlinux ne fait aucune opération système *depuis* le sandbox : il shelle
vers des binaires (`nmcli`, `ip`, `pkexec`, `ssh`, `mount.cifs`, `nmap`,
`xfreerdp`, …) qui doivent agir sur le **vrai** NetworkManager, le vrai
`/etc/hosts`, les vrais montages. Sandboxer chacun de ces outils
individuellement (device=all, filesystem=host, système D-Bus par outil…)
viderait le sandbox de son sens sans rien apporter — ce sont des outils
d'administration système par nature.

À la place, `host-bin/` contient un script générique
(`flatpak-spawn --host "$(basename "$0")" "$@"`) symlinké sous chacun de
ces noms de binaires, et placé en tête du `PATH` de l'app
(`--env=PATH=/app/bin/host-bin:...`). Le code Python de nmlinux n'a pas
besoin de savoir qu'il tourne dans un sandbox — `subprocess.run(["nmcli", ...])`
résout `nmcli` vers le shim, qui rebondit sur l'hôte via
`--talk-name=org.freedesktop.Flatpak`.

**Limite connue de cette approche :** un chemin de fichier passé à une
commande exécutée ainsi doit être visible depuis l'espace de noms de
montage de l'hôte — le `/tmp` privé du sandbox ne l'est pas. C'est pour ça
que `nmlinux/core/flatpak_shim.py` redirige les fichiers temporaires et
scripts d'aide (`smb_mount_helper.py`, `tftp_helper.py`, l'écriture de
`/etc/hosts`) vers `$XDG_CACHE_HOME/nmlinux/tmp`, le seul répertoire que
Flatpak fait pointer vers un vrai chemin hôte
(`~/.var/app/io.github.thongor77.NMLinux/cache/...`). Voir DT-18 dans
`docs/Decisions-Techniques.md`.

**Simplification volontaire pour ce premier passage :** `--filesystem=home`
est large (accès à tout le `$HOME`), au lieu de portails
`org.freedesktop.portal.FileChooser` + permissions ciblées
(`~/.ssh`, `~/mnt`, `xdg-documents`). À resserrer si ce manifest doit un
jour viser Flathub.

## PySide6 : pourquoi `io.qt.PySide.BaseApp` et pas un module pip

`flatpak-pip-generator` refuse tout net de générer un module pour PySide6
(« Please use the baseapp https://github.com/flathub/io.qt.PySide.BaseApp »).
Le wheel PyPI est énorme et embarque son propre Qt ; le BaseApp le compile
au contraire contre le Qt du runtime `org.kde.Platform`, donc pas de Qt en
double. C'est le chemin que Flathub a construit pour ce problème précis —
seuls `ptyprocess`, `pyte`, `tftpy` et `hatchling` (backend de build) sont
donc pip-générés (module `python3-requirements` dans le manifest).
`BASEAPP_REMOVE_WEBENGINE=1`/`BASEAPP_DISABLE_NUMPY=1` retirent deux
composants du BaseApp que nmlinux n'utilise pas (réduit la taille du build).

## Prérequis

```bash
flatpak install flathub org.kde.Platform//6.11 org.kde.Sdk//6.11 io.qt.PySide.BaseApp//6.11
sudo pacman -S flatpak-builder   # ou distro équivalente
```

## 1. Régénérer les sources pip (si `pyproject.toml` change)

Le module `python3-requirements` du manifest (`ptyprocess`, `pyte`, `tftpy`,
`hatchling` — PAS PySide6, voir ci-dessus) est déjà commité avec ses
URLs + sha256 PyPI épinglés. Pour le régénérer :

```bash
curl -sLO https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator.py
uv run --with pyyaml flatpak-pip-generator.py \
    --yaml --output python3-requirements \
    ptyprocess pyte tftpy hatchling
```

Ça produit `python3-requirements.yaml` — coller son contenu (le bloc
`modules:` imbriqué) dans le manifest à la place du module
`python3-requirements` existant.

## 2. Build

```bash
cd packaging/flatpak
flatpak-builder --user --install --force-clean build-dir io.github.thongor77.NMLinux.yml
```

## 3. Lancer

```bash
flatpak run io.github.thongor77.NMLinux
```

## Distribuer — bundle `.flatpak` pour GitHub Releases

Pas de Flathub pour l'instant (voir plus haut : `--filesystem=home` +
`flatpak-spawn --host` sont exactement ce que la review Flathub resserre en
priorité — chantier à part si un jour visé). Reste modeste : un fichier
`.flatpak` unique joint à chaque release GitHub, comme le wheel et
l'AppImage déjà distribués.

```bash
bash packaging/flatpak/build-bundle.sh
# → dist/NMLinux-X.Y.Z-x86_64.flatpak
```

Le bundle embarque `--runtime-repo=https://flathub.org/repo/flathub.flatpakrepo` :
côté utilisateur, `flatpak install NMLinux-X.Y.Z-x86_64.flatpak` propose
d'ajouter Flathub et d'y récupérer `org.kde.Platform`/`io.qt.PySide.BaseApp`
automatiquement s'ils ne sont pas déjà installés — pas besoin d'un dépôt
ostree séparé à héberger. Intégré à la procédure de release complète dans
`docs/Maintenance-IA.md` §Release.

Validé en conditions réelles (2026-08-03) : build → `flatpak install --user`
depuis le fichier `.flatpak` → `flatpak run` sans erreur.

## Dépannage

- **Un module (`nmap`, `mtr`, `xfreerdp`…) répond "introuvable" alors qu'il
  est installé** : c'est un outil hôte, pas un problème de sandbox tant que
  le shim existe dans `host-bin/`. S'il manque un nom, l'ajouter à la liste
  de symlinks et au module `nmlinux` du manifest.
- **`pkexec` ne montre pas de popup d'authentification** : `flatpak-spawn
  --host pkexec` doit être lancé par un `polkit` fonctionnel côté hôte
  (normal sur KDE Linux) — sans agent polkit actif ça échoue silencieusement.
- **`pip3 install .` du module `nmlinux` ne trouve pas PySide6** : normal,
  il n'est jamais téléchargé — vérifier qu'il est bien fourni par
  `io.qt.PySide.BaseApp//6.11` (déjà installé comme `base:` dans le
  manifest) plutôt que manquant du `python3-requirements`.
