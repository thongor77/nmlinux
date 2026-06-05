# SSH Key Manager — Design Spec
_Date : 2026-06-05_

## Objectif

Ajouter un module **SSH Key Manager** à NMLinux permettant de lister, générer, copier et déployer des clés SSH, ainsi que de supprimer des paires existantes — le tout sans quitter l'application.

---

## Architecture

Un seul fichier : `nmlinux/pages/ssh_keys.py`.  
Pattern identique à `hosts.py` (table + toolbar + status bar).  
Terminal inline pour le déploiement, pattern repris de `ssh.py`.  
Pas de module `core/` séparé — tout via `subprocess` et `ssh-keygen`.

---

## Composants

### `_scan_keys(ssh_dir: Path) -> list[dict]`

Scanne `~/.ssh/*.pub`. Pour chaque fichier `.pub` dont la clé privée correspondante existe, appelle `ssh-keygen -l -f <pubkey>` pour extraire :
- `file` : nom de base (ex. `id_ed25519`)
- `type` : algorithme (ex. `ED25519`, `RSA`)
- `bits` : taille en bits
- `fingerprint` : hash SHA256
- `comment` : commentaire de la clé
- `pub_path` / `priv_path` : chemins complets

Les paires incomplètes (`.pub` sans clé privée) sont ignorées silencieusement.

---

### `_KeyGenDialog(QDialog)`

Dialog de génération de clé. Champs :

| Champ | Widget | Défaut |
|---|---|---|
| Type | QComboBox | Ed25519 (RSA 4096 en option) |
| Nom du fichier | QLineEdit | `id_ed25519` ou `id_rsa` selon type |
| Commentaire | QLineEdit | `user@hostname` |
| Passphrase | QLineEdit (password) | vide = sans passphrase |
| Confirmation | QLineEdit (password) | vide |

Règles :
- Le nom de fichier est mis à jour automatiquement quand on change le type (sauf si l'utilisateur l'a modifié manuellement).
- Bouton OK désactivé si `passphrase != confirmation`.
- Si `~/.ssh/<filename>` existe déjà : dialog secondaire « Écraser ? » avant de lancer.
- Si `~/.ssh/` n'existe pas : créé automatiquement avec `chmod 700`.

Lancement : `ssh-keygen -t ed25519 -f ~/.ssh/<name> -C "<comment>" -N "<passphrase>"` via `QThread`.

---

### `_DeployBar(QWidget)`

Widget terminal inline, caché par défaut, affiché sous la table lors du clic sur **Déployer**.

Champs :
- `user@host` (QLineEdit)
- Port (QLineEdit, défaut `22`)
- Bouton **Lancer** / **Fermer**

Terminal : `QTextEdit` en lecture seule + `QProcess` interactif.  
Commande : `ssh-copy-id -i <selected_key.pub> -p <port> <user@host>`  
`QProcess` en mode `MergedChannels`, les sorties s_affichent en temps réel.  
Vérifie `shutil.which("ssh-copy-id")` avant de lancer — message d'erreur clair si absent.  
Clic sur **Fermer** : `QProcess.terminate()` si un processus est en cours, puis hide du widget.

---

### `SshKeysPage(QWidget)`

Page principale.

**Toolbar :**
- Générer
- Copier clé publique _(désactivé si aucune sélection)_
- Déployer _(désactivé si aucune sélection)_
- Supprimer _(désactivé si aucune sélection)_
- Actualiser

**Table** (`QTableWidget`, 5 colonnes) :

| # | Colonne | Resize |
|---|---|---|
| 0 | Fichier | ResizeToContents |
| 1 | Type | ResizeToContents |
| 2 | Bits | ResizeToContents |
| 3 | Commentaire | Stretch |
| 4 | Fingerprint | ResizeToContents |

- Sélection par ligne, pas d'édition inline.
- `AlternatingRowColors`.
- `_DeployBar` en bas (hidden/shown selon action Déployer).

**Status bar** : label texte gris, messages colorés (vert = succès, rouge = erreur).

---

## Actions

| Action | Comportement |
|---|---|
| **Générer** | Ouvre `_KeyGenDialog`, lance `ssh-keygen` en QThread, rafraîchit la table |
| **Copier clé publique** | Lit le `.pub` sélectionné, `QApplication.clipboard().setText(content)`, status « Copié » |
| **Déployer** | Affiche `_DeployBar` en bas, pré-remplit la clé sélectionnée |
| **Supprimer** | Dialog de confirmation avec nom explicite, `os.unlink` des deux fichiers, rafraîchit |
| **Actualiser** | Re-scanne `~/.ssh/`, rafraîchit la table |

---

## CLI Bar

| Contexte | Commande affichée |
|---|---|
| Page ouverte | `ls -la ~/.ssh/` |
| Génération Ed25519 | `ssh-keygen -t ed25519 -f ~/.ssh/<name> -C "<comment>"` |
| Génération RSA | `ssh-keygen -t rsa -b 4096 -f ~/.ssh/<name> -C "<comment>"` |
| Déploiement | `ssh-copy-id -i ~/.ssh/<name>.pub -p <port> <user@host>` |

---

## i18n

Préfixe `ssh_keys_`. 4 langues : fr, en, de, es.

Clés principales :
```
ssh_keys_btn_generate, ssh_keys_btn_copy_pub, ssh_keys_btn_deploy
ssh_keys_btn_delete, ssh_keys_btn_refresh
ssh_keys_col_file, ssh_keys_col_type, ssh_keys_col_bits
ssh_keys_col_comment, ssh_keys_col_fingerprint
ssh_keys_dlg_gen_title, ssh_keys_dlg_gen_type, ssh_keys_dlg_gen_file
ssh_keys_dlg_gen_comment, ssh_keys_dlg_gen_passphrase, ssh_keys_dlg_gen_confirm
ssh_keys_dlg_overwrite_title, ssh_keys_dlg_overwrite_msg
ssh_keys_dlg_del_title, ssh_keys_dlg_del_msg
ssh_keys_deploy_user_host, ssh_keys_deploy_port, ssh_keys_deploy_btn_run
ssh_keys_deploy_btn_close, ssh_keys_deploy_no_tool
ssh_keys_generated, ssh_keys_copied, ssh_keys_deleted
ssh_keys_err_passphrase_mismatch, ssh_keys_err_keygen
nav_ssh_keys, nav_hint_ssh_keys
```

---

## Enregistrement (`window.py`)

```python
from nmlinux.pages.ssh_keys import SshKeysPage

# Dans la liste des pages, après l'entrée SSH :
(
    ("dialog-password", "security-high", "changes-prevent"),
    "SSH Keys", SshKeysPage,
    tr("nav_hint_ssh_keys"),
),
```

---

## Dépendances système

| Outil | Usage | Disponibilité |
|---|---|---|
| `ssh-keygen` | Génération + fingerprint | Toujours présent (openssh) |
| `ssh-copy-id` | Déploiement | Présent sur la plupart des distros (openssh-client) |

Aucune dépendance Python supplémentaire.
