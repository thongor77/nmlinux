from __future__ import annotations

import time as _time

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem,
    QStackedWidget,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTextEdit,
    QFrame, QGroupBox, QSplitter, QFileDialog,
    QMessageBox, QToolButton, QApplication, QPlainTextEdit,
    QComboBox, QInputDialog, QMenu,
)
from PySide6.QtGui import (
    QIcon, QFont, QColor, QPalette, QKeyEvent,
    QFontDatabase, QTextCursor,
)
from PySide6.QtCore import Qt, QTimer

from nmlinux.core.ssh import SshConnection, SshGroup, SshStore, build_ssh_args
from nmlinux.core.terminal import SshWorker, ERASE_EOL, CURSOR_RIGHT
from nmlinux.core.i18n import tr

_EMPTY    = 0
_DETAIL   = 1
_FORM     = 2
_TERMINAL = 3

_CTRL_MAP = {
    Qt.Key.Key_C: '\x03',
    Qt.Key.Key_D: '\x04',
    Qt.Key.Key_Z: '\x1a',
    Qt.Key.Key_L: '\x0c',
    Qt.Key.Key_A: '\x01',
    Qt.Key.Key_E: '\x05',
    Qt.Key.Key_U: '\x15',
    Qt.Key.Key_K: '\x0b',
    Qt.Key.Key_W: '\x17',
    Qt.Key.Key_R: '\x12',
}

_KEY_MAP = {
    Qt.Key.Key_Up:       '\x1b[A',
    Qt.Key.Key_Down:     '\x1b[B',
    Qt.Key.Key_Right:    '\x1b[C',
    Qt.Key.Key_Left:     '\x1b[D',
    Qt.Key.Key_Home:     '\x1b[H',
    Qt.Key.Key_End:      '\x1b[F',
    Qt.Key.Key_Delete:   '\x1b[3~',
    Qt.Key.Key_PageUp:   '\x1b[5~',
    Qt.Key.Key_PageDown: '\x1b[6~',
    Qt.Key.Key_Insert:   '\x1b[2~',
    Qt.Key.Key_F1:       '\x1bOP',
    Qt.Key.Key_F2:       '\x1bOQ',
    Qt.Key.Key_F3:       '\x1bOR',
    Qt.Key.Key_F4:       '\x1bOS',
    Qt.Key.Key_F5:       '\x1b[15~',
    Qt.Key.Key_Backtab:  '\x1b[Z',    # Shift+Tab (reverse completion)
}


# ── Terminal output widget ─────────────────────────────────────────────────

class _TerminalView(QWidget):
    def __init__(self, worker_box: list[SshWorker | None]) -> None:
        super().__init__()
        self._wref = worker_box
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)
        self._dedup_ts: int = -1
        self._dedup_sig: tuple = ()
        self._dedup_mono: float = 0.0

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(200)
        self._resize_timer.timeout.connect(self._notify_pty_resize)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._out.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._out.setMaximumBlockCount(8000)

        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self._out.setFont(mono)

        pal = QPalette(self._out.palette())
        pal.setColor(QPalette.ColorRole.Base,            QColor("#1e1e2e"))
        pal.setColor(QPalette.ColorRole.Text,            QColor("#cdd6f4"))
        pal.setColor(QPalette.ColorRole.Highlight,       QColor("#313244"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#cdd6f4"))
        self._out.setPalette(pal)
        self._out.viewport().installEventFilter(self)
        layout.addWidget(self._out)

    def focusNextPrevChild(self, next: bool) -> bool:
        # Prevent Qt from using Tab/Shift-Tab for focus traversal so the
        # key reaches keyPressEvent and is forwarded to the remote shell.
        return False

    def eventFilter(self, obj, event) -> bool:
        from PySide6.QtCore import QEvent
        if obj is self._out.viewport() and event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonDblClick,
        ):
            self.setFocus()
        return False

    def keyPressEvent(self, event: QKeyEvent) -> None:
        w = self._wref[0]
        if w is None:
            return

        key = event.key()
        if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt,
                   Qt.Key.Key_Meta, Qt.Key.Key_AltGr, Qt.Key.Key_CapsLock,
                   Qt.Key.Key_NumLock, Qt.Key.Key_ScrollLock, Qt.Key.Key_Super_L,
                   Qt.Key.Key_Super_R, Qt.Key.Key_Hyper_L, Qt.Key.Key_Hyper_R):
            event.accept()
            return

        ts = event.timestamp()
        if ts:
            if ts == self._dedup_ts:
                event.accept()
                return
            self._dedup_ts = ts
        else:
            now = _time.monotonic()
            sig = (key, event.text(), int(event.modifiers()))
            if sig == self._dedup_sig and now - self._dedup_mono < 0.010:
                event.accept()
                return
            self._dedup_sig = sig
            self._dedup_mono = now

        mods = event.modifiers()

        if mods == (Qt.KeyboardModifier.ControlModifier |
                    Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_C:
                self._out.copy(); event.accept(); return
            if key == Qt.Key.Key_V:
                txt = QApplication.clipboard().text()
                if txt:
                    w.write(txt)
                event.accept(); return

        if mods == Qt.KeyboardModifier.ControlModifier:
            seq = _CTRL_MAP.get(key)
            if seq:
                w.write(seq); event.accept(); return

        if mods in (Qt.KeyboardModifier.NoModifier,
                    Qt.KeyboardModifier.ShiftModifier):
            seq = _KEY_MAP.get(key)
            if seq:
                w.write(seq); event.accept(); return

        txt = event.text()
        if txt:
            w.write('\x7f' if txt == '\x08' else txt)
            event.accept()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._resize_timer.start()  # restart — fires 200 ms after last resize

    def _notify_pty_resize(self) -> None:
        w = self._wref[0]
        if w is None:
            return
        fm = self._out.fontMetrics()
        char_w = fm.horizontalAdvance('M')
        char_h = fm.height()
        if char_w <= 0 or char_h <= 0:
            return
        vp = self._out.viewport()
        cols = max(20, vp.width()  // char_w)
        rows = max(5,  vp.height() // char_h)
        w.resize(rows, cols)

    def pty_dims(self) -> tuple[int, int]:
        """Return (rows, cols) based on current widget size."""
        fm = self._out.fontMetrics()
        char_w = fm.horizontalAdvance('M')
        char_h = fm.height()
        if char_w <= 0 or char_h <= 0:
            return (24, 80)
        vp = self._out.viewport()
        cols = max(20, vp.width()  // char_w)
        rows = max(5,  vp.height() // char_h)
        return (rows, cols)

    def clear(self)                    -> None:    self._out.clear()
    def textCursor(self):                          return self._out.textCursor()
    def setTextCursor(self, c)         -> None:    self._out.setTextCursor(c)
    def ensureCursorVisible(self)      -> None:    self._out.ensureCursorVisible()


# ── SSH page ───────────────────────────────────────────────────────────────

class SshPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._store       = SshStore()
        self._groups, self._connections = self._store.load()
        self._editing_id: str | None = None
        self._worker_box: list[SshWorker | None] = [None]

        self._build_ui()
        self._refresh_list()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([220, 700])
        root.addWidget(splitter)

    # ── Left panel ─────────────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)

        btn_new_conn = QPushButton(QIcon.fromTheme("list-add"), " " + tr("ssh_new_conn_btn"))
        btn_new_conn.clicked.connect(self._on_new)
        btn_new_grp  = QPushButton(QIcon.fromTheme("folder-new"), " " + tr("ssh_new_grp_btn"))
        btn_new_grp.clicked.connect(self._on_new_group)
        layout.addWidget(btn_new_conn)
        layout.addWidget(btn_new_grp)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setFrameShape(QFrame.Shape.NoFrame)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._tree, 1)
        return panel

    # ── Right panel ────────────────────────────────────────────────────────

    def _build_right(self) -> QStackedWidget:
        self._right = QStackedWidget()
        self._right.addWidget(self._build_empty())
        self._right.addWidget(self._build_detail())
        self._right.addWidget(self._build_form())
        self._right.addWidget(self._build_terminal())
        return self._right

    def _build_empty(self) -> QWidget:
        w = QWidget()
        lbl = QLabel(tr("ssh_empty_state"))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: palette(mid); font-size: 14px;")
        QVBoxLayout(w).addWidget(lbl)
        return w

    def _build_detail(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._det_name = QLabel()
        self._det_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._det_subtitle = QLabel()
        self._det_subtitle.setStyleSheet("color: palette(mid);")
        self._det_group_path = QLabel()
        self._det_group_path.setStyleSheet("color: palette(mid); font-style: italic;")
        layout.addWidget(self._det_name)
        layout.addWidget(self._det_subtitle)
        layout.addWidget(self._det_group_path)

        card = QGroupBox()
        form = QFormLayout(card)
        form.setHorizontalSpacing(20)
        self._det: dict[str, QLabel] = {}
        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        for key, label in [
            ("host",     "Hôte"),
            ("port",     "Port"),
            ("username", "Utilisateur"),
            ("key_path", "Clé SSH"),
            ("command",  "Commande"),
            ("notes",    "Notes"),
        ]:
            val = QLabel()
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setWordWrap(True)
            if key == "command":
                val.setFont(mono)
                val.setStyleSheet("color: palette(link);")
            self._det[key] = val
            form.addRow(label + " :", val)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        self._btn_connect = QPushButton(
            QIcon.fromTheme("utilities-terminal"), " Se connecter")
        self._btn_connect.setDefault(True)
        self._btn_connect.clicked.connect(self._on_connect)
        btn_copy = QPushButton(QIcon.fromTheme("edit-copy"), " Copier")
        btn_copy.setToolTip("Copier la commande SSH")
        btn_copy.clicked.connect(self._on_copy)
        btn_edit = QPushButton(QIcon.fromTheme("document-edit"), " Modifier")
        btn_edit.clicked.connect(self._on_edit)
        btn_del  = QPushButton(QIcon.fromTheme("edit-delete"), " Supprimer")
        btn_del.clicked.connect(self._on_delete)
        row.addWidget(self._btn_connect)
        row.addWidget(btn_copy)
        row.addWidget(btn_edit)
        row.addStretch(1)
        row.addWidget(btn_del)
        layout.addLayout(row)
        return w

    def _build_form(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._form_title = QLabel()
        self._form_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._form_title)

        card = QGroupBox()
        form = QFormLayout(card)
        form.setHorizontalSpacing(20)

        self._f_name  = QLineEdit(); self._f_name.setPlaceholderText("Mon serveur")
        self._f_group = QComboBox()
        self._f_host  = QLineEdit(); self._f_host.setPlaceholderText("192.168.1.100")
        self._f_port  = QSpinBox();  self._f_port.setRange(1, 65535); self._f_port.setValue(22)
        self._f_user  = QLineEdit(); self._f_user.setPlaceholderText("root")
        self._f_notes = QTextEdit(); self._f_notes.setMaximumHeight(80)

        key_row = QHBoxLayout(); key_row.setSpacing(4)
        self._f_key = QLineEdit()
        self._f_key.setPlaceholderText("~/.ssh/id_ed25519  (vide = mot de passe)")
        btn_browse = QToolButton()
        btn_browse.setIcon(QIcon.fromTheme("document-open"))
        btn_browse.clicked.connect(self._on_browse_key)
        key_row.addWidget(self._f_key, 1); key_row.addWidget(btn_browse)

        form.addRow("Nom :",         self._f_name)
        form.addRow("Groupe :",      self._f_group)
        form.addRow("Hôte * :",      self._f_host)
        form.addRow("Port :",        self._f_port)
        form.addRow("Utilisateur :", self._f_user)
        form.addRow("Clé SSH :",     key_row)
        form.addRow("Notes :",       self._f_notes)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        btn_save   = QPushButton(QIcon.fromTheme("document-save"), " Enregistrer")
        btn_save.setDefault(True); btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton(QIcon.fromTheme("dialog-cancel"), " Annuler")
        btn_cancel.clicked.connect(self._on_cancel)
        row.addWidget(btn_save); row.addWidget(btn_cancel); row.addStretch(1)
        layout.addLayout(row)
        return w

    def _build_terminal(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(12, 6, 12, 6)
        self._term_dot   = QLabel("●")
        self._term_dot.setStyleSheet("color: #a6e3a1; font-size: 16px;")
        self._term_label = QLabel()
        self._term_label.setStyleSheet("font-weight: bold;")
        btn_disc = QPushButton(QIcon.fromTheme("network-disconnect"), " Déconnecter")
        btn_disc.clicked.connect(self._on_disconnect)
        h_row.addWidget(self._term_dot)
        h_row.addWidget(self._term_label, 1)
        h_row.addWidget(btn_disc)
        layout.addWidget(header)

        self._term_view = _TerminalView(self._worker_box)
        layout.addWidget(self._term_view, 1)
        return w

    # ── Tree helpers ───────────────────────────────────────────────────────

    def _group_path(self, group_id: str) -> str:
        """Return 'Parent > Child' breadcrumb for a group id."""
        parts: list[str] = []
        gid = group_id
        while gid:
            grp = next((g for g in self._groups if g.id == gid), None)
            if grp is None:
                break
            parts.insert(0, grp.name)
            gid = grp.parent_id
        return " > ".join(parts)

    def _build_tree_children(
        self,
        parent_item: QTreeWidgetItem,
        parent_group_id: str,
        icon_conn: QIcon,
        icon_grp: QIcon,
    ) -> None:
        # Sub-groups first
        for group in self._groups:
            if group.parent_id == parent_group_id:
                g_item = QTreeWidgetItem(parent_item, [group.name])
                g_item.setIcon(0, icon_grp)
                g_item.setData(0, Qt.ItemDataRole.UserRole, ('group', group.id))
                g_item.setExpanded(True)
                f = g_item.font(0); f.setBold(True); g_item.setFont(0, f)
                self._build_tree_children(g_item, group.id, icon_conn, icon_grp)

        # Then connections belonging to this group
        for conn in self._connections:
            if conn.group_id == parent_group_id:
                c_item = QTreeWidgetItem(parent_item, [conn.display_name])
                c_item.setIcon(0, icon_conn)
                c_item.setToolTip(0, conn.subtitle)
                c_item.setData(0, Qt.ItemDataRole.UserRole, ('conn', conn.id))

    def _refresh_list(self, select_conn_id: str | None = None) -> None:
        self._tree.blockSignals(True)
        self._tree.clear()

        icon_conn = QIcon.fromTheme("utilities-terminal")
        icon_grp  = QIcon.fromTheme("folder")
        self._build_tree_children(
            self._tree.invisibleRootItem(), "", icon_conn, icon_grp
        )

        self._tree.blockSignals(False)

        if select_conn_id:
            self._select_conn(select_conn_id)
        else:
            self._select_first_conn()

    def _select_conn(self, conn_id: str) -> bool:
        def walk(parent: QTreeWidgetItem) -> bool:
            for i in range(parent.childCount()):
                child = parent.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == 'conn' and data[1] == conn_id:
                    self._tree.setCurrentItem(child)
                    return True
                if walk(child):
                    return True
            return False
        return walk(self._tree.invisibleRootItem())

    def _select_first_conn(self) -> None:
        def walk(parent: QTreeWidgetItem) -> bool:
            for i in range(parent.childCount()):
                child = parent.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == 'conn':
                    self._tree.setCurrentItem(child)
                    return True
                if walk(child):
                    return True
            return False
        if not walk(self._tree.invisibleRootItem()):
            self._right.setCurrentIndex(_EMPTY)

    def _current_conn(self) -> SshConnection | None:
        item = self._tree.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None or data[0] != 'conn':
            return None
        return next((c for c in self._connections if c.id == data[1]), None)

    def _populate_group_combo(self, current_group_id: str = "") -> None:
        self._f_group.blockSignals(True)
        self._f_group.clear()
        self._f_group.addItem("— Aucun groupe —", "")

        def add_group(grp: SshGroup, indent: int) -> None:
            prefix = "    " * indent
            self._f_group.addItem(f"{prefix}{grp.name}", grp.id)
            for sub in self._groups:
                if sub.parent_id == grp.id:
                    add_group(sub, indent + 1)

        for grp in self._groups:
            if not grp.parent_id:
                add_group(grp, 0)

        idx = self._f_group.findData(current_group_id)
        self._f_group.setCurrentIndex(idx if idx >= 0 else 0)
        self._f_group.blockSignals(False)

    # ── Slots — selection ──────────────────────────────────────────────────

    def _on_selection_changed(
        self, current: QTreeWidgetItem | None, _prev
    ) -> None:
        if self._right.currentIndex() == _TERMINAL:
            return
        if current is None:
            self._right.setCurrentIndex(_EMPTY)
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if data is None or data[0] != 'conn':
            self._right.setCurrentIndex(_EMPTY)
            return
        conn = next((c for c in self._connections if c.id == data[1]), None)
        if conn:
            self._show_detail(conn)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == 'conn':
            conn = next((c for c in self._connections if c.id == data[1]), None)
            if conn:
                self._start_session(conn)

    def _on_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if item is None:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return
        kind, item_id = data

        menu = QMenu(self)
        if kind == 'conn':
            conn = next((c for c in self._connections if c.id == item_id), None)
            if conn is None:
                return
            act_connect = menu.addAction(
                QIcon.fromTheme("utilities-terminal"), "Se connecter"
            )
            menu.addSeparator()
            act_edit = menu.addAction(QIcon.fromTheme("document-edit"), "Modifier")
            act_del  = menu.addAction(QIcon.fromTheme("edit-delete"),   "Supprimer")
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_connect:
                self._start_session(conn)
            elif act == act_edit:
                self._tree.setCurrentItem(item)
                self._on_edit()
            elif act == act_del:
                self._tree.setCurrentItem(item)
                self._on_delete()

        elif kind == 'group':
            grp = next((g for g in self._groups if g.id == item_id), None)
            if grp is None:
                return
            act_rename  = menu.addAction(QIcon.fromTheme("document-edit"), "Renommer")
            act_add_sub = menu.addAction(QIcon.fromTheme("folder-new"),    "Ajouter un sous-groupe")
            menu.addSeparator()
            act_del = menu.addAction(QIcon.fromTheme("edit-delete"), "Supprimer le groupe")
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_rename:
                self._rename_group(item_id)
            elif act == act_add_sub:
                self._new_subgroup(item_id)
            elif act == act_del:
                self._delete_group(item_id)

    # ── Slots — detail ─────────────────────────────────────────────────────

    def _show_detail(self, conn: SshConnection) -> None:
        self._det_name.setText(conn.display_name)
        self._det_subtitle.setText(conn.subtitle)
        path = self._group_path(conn.group_id)
        self._det_group_path.setText(path)
        self._det_group_path.setVisible(bool(path))
        self._det["host"].setText(conn.host)
        self._det["port"].setText(str(conn.port))
        self._det["username"].setText(conn.username or "—")
        self._det["key_path"].setText(conn.key_path or "— (mot de passe)")
        self._det["command"].setText(conn.ssh_command)
        self._det["notes"].setText(conn.notes or "")
        self._right.setCurrentIndex(_DETAIL)

    def _on_connect(self) -> None:
        conn = self._current_conn()
        if conn:
            self._start_session(conn)

    def _on_copy(self) -> None:
        conn = self._current_conn()
        if conn:
            QApplication.clipboard().setText(conn.ssh_command)

    def _on_edit(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        self._editing_id = conn.id
        self._form_title.setText("Modifier la connexion")
        self._populate_group_combo(conn.group_id)
        self._f_name.setText(conn.name)
        self._f_host.setText(conn.host)
        self._f_port.setValue(conn.port)
        self._f_user.setText(conn.username)
        self._f_key.setText(conn.key_path)
        self._f_notes.setPlainText(conn.notes)
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_delete(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        ans = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer « {conn.display_name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        self._connections = [c for c in self._connections if c.id != conn.id]
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    # ── Slots — form ───────────────────────────────────────────────────────

    def _on_new(self) -> None:
        # Pre-select the group that is currently highlighted in the tree
        preselect = ""
        item = self._tree.currentItem()
        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'group':
                preselect = data[1]

        self._editing_id = None
        self._form_title.setText("Nouvelle connexion")
        self._populate_group_combo(preselect)
        self._f_name.clear()
        self._f_host.clear()
        self._f_port.setValue(22)
        self._f_user.clear()
        self._f_key.clear()
        self._f_notes.clear()
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_save(self) -> None:
        import uuid
        host = self._f_host.text().strip()
        if not host:
            QMessageBox.warning(self, "Champ requis", "L'hôte est requis.")
            self._f_host.setFocus()
            return
        updated = SshConnection(
            id       = self._editing_id or str(uuid.uuid4()),
            name     = self._f_name.text().strip() or host,
            host     = host,
            port     = self._f_port.value(),
            username = self._f_user.text().strip(),
            key_path = self._f_key.text().strip(),
            notes    = self._f_notes.toPlainText().strip(),
            group_id = self._f_group.currentData() or "",
        )
        if self._editing_id:
            self._connections = [
                updated if c.id == self._editing_id else c
                for c in self._connections
            ]
        else:
            self._connections.append(updated)
        self._store.save(self._groups, self._connections)
        self._refresh_list(select_conn_id=updated.id)

    def _on_cancel(self) -> None:
        conn = self._current_conn()
        if conn:
            self._show_detail(conn)
        else:
            self._right.setCurrentIndex(_EMPTY)

    def _on_browse_key(self) -> None:
        from pathlib import Path
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner une clé SSH",
            str(Path.home() / ".ssh"),
            "Clés SSH (*id_* *.pem);;Tous (*)",
        )
        if path:
            self._f_key.setText(path)

    # ── Slots — group management ───────────────────────────────────────────

    def _on_new_group(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Nouveau groupe", "Nom du groupe :"
        )
        if not ok or not name.strip():
            return

        # Ask for parent only if there are existing top-level groups
        top_groups = [g for g in self._groups if not g.parent_id]
        parent_id = ""
        if top_groups:
            choices = ["— Niveau racine —"] + [g.name for g in top_groups]
            choice, ok2 = QInputDialog.getItem(
                self, "Groupe parent", "Placer dans :", choices, 0, False
            )
            if not ok2:
                return
            if choice != choices[0]:
                idx = choices.index(choice) - 1
                parent_id = top_groups[idx].id

        self._groups.append(SshGroup(name=name.strip(), parent_id=parent_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _new_subgroup(self, parent_group_id: str) -> None:
        parent = next((g for g in self._groups if g.id == parent_group_id), None)
        if parent is None:
            return
        name, ok = QInputDialog.getText(
            self, "Nouveau sous-groupe",
            f"Sous-groupe de « {parent.name} » :"
        )
        if not ok or not name.strip():
            return
        self._groups.append(SshGroup(name=name.strip(), parent_id=parent_group_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _rename_group(self, group_id: str) -> None:
        grp = next((g for g in self._groups if g.id == group_id), None)
        if grp is None:
            return
        name, ok = QInputDialog.getText(
            self, "Renommer", "Nouveau nom :", text=grp.name
        )
        if ok and name.strip():
            grp.name = name.strip()
            self._store.save(self._groups, self._connections)
            self._refresh_list()

    def _delete_group(self, group_id: str) -> None:
        grp = next((g for g in self._groups if g.id == group_id), None)
        if grp is None:
            return
        ans = QMessageBox.question(
            self, "Supprimer le groupe",
            f"Supprimer « {grp.name} » ?\n"
            "Les connexions qu'il contient seront déplacées à la racine.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        # Collect the group + all its subgroups
        ids_to_remove: set[str] = set()

        def collect(gid: str) -> None:
            ids_to_remove.add(gid)
            for sub in self._groups:
                if sub.parent_id == gid:
                    collect(sub.id)

        collect(group_id)

        for conn in self._connections:
            if conn.group_id in ids_to_remove:
                conn.group_id = ""

        self._groups = [g for g in self._groups if g.id not in ids_to_remove]
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    # ── Slots — terminal ───────────────────────────────────────────────────

    def _start_session(self, conn: SshConnection) -> None:
        self._stop_worker()
        rows, cols = self._term_view.pty_dims()
        worker = SshWorker(build_ssh_args(conn), rows=rows, cols=cols)
        worker.output.connect(self._on_term_output)
        worker.exited.connect(self._on_term_exited)
        worker.clear_screen.connect(self._term_view.clear)
        self._worker_box[0] = worker

        self._term_view.clear()
        self._term_label.setText(f"{conn.display_name}  —  {conn.subtitle}")
        self._term_dot.setStyleSheet("color: #a6e3a1; font-size: 16px;")
        self._right.setCurrentIndex(_TERMINAL)
        self._term_view.setFocus()
        worker.start()

    def _on_term_output(self, text: str) -> None:
        # Character-by-character terminal output processor.
        # The cursor is NOT reset to End on each call — it persists between reads
        # so that \r in one read and CUF/EL in the next read work as a unit.
        # Normal text always ends up appending because the cursor stays at End
        # after any plain-text insert, and is only moved by \r / ERASE_EOL / CURSOR_RIGHT.
        cursor = self._term_view.textCursor()

        i = 0
        n = len(text)
        while i < n:
            ch = text[i]

            if ch == '\r':
                if i + 1 < n and text[i + 1] == '\n':
                    cursor.insertText('\n')
                    i += 2
                else:
                    # bare CR: reposition to start of line; erase comes from \x1b[K
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    i += 1

            elif ch == ERASE_EOL:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                   QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                i += 1

            elif ch == CURSOR_RIGHT:
                if not cursor.atBlockEnd():
                    cursor.movePosition(QTextCursor.MoveOperation.Right)
                i += 1

            elif ch == '\x08':
                if not cursor.atBlockStart():
                    cursor.movePosition(QTextCursor.MoveOperation.Left,
                                       QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                i += 1

            elif ch == '\n':
                cursor.insertText('\n')
                i += 1

            else:
                j = i + 1
                while j < n and text[j] not in ('\r', '\x08', '\n', ERASE_EOL, CURSOR_RIGHT):
                    j += 1
                cursor.insertText(text[i:j])
                i = j

        self._term_view.setTextCursor(cursor)
        self._term_view.ensureCursorVisible()

    def _on_term_exited(self, code: int) -> None:
        self._worker_box[0] = None
        self._term_dot.setStyleSheet("color: #f38ba8; font-size: 16px;")
        cursor = self._term_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"\n\n── Session terminée (code {code}) ──\n")
        self._term_view.setTextCursor(cursor)
        self._term_view.ensureCursorVisible()

    def _on_disconnect(self) -> None:
        self._stop_worker()
        conn = self._current_conn()
        if conn:
            self._show_detail(conn)
        else:
            self._right.setCurrentIndex(_EMPTY)

    def _stop_worker(self) -> None:
        w = self._worker_box[0]
        if w is not None:
            w.output.disconnect()
            w.exited.disconnect()
            w.clear_screen.disconnect()
            w.stop()
            self._worker_box[0] = None

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._stop_worker()
        super().closeEvent(event)
