from __future__ import annotations

import uuid

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem,
    QStackedWidget,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTextEdit,
    QFrame, QGroupBox, QSplitter, QCheckBox,
    QMessageBox, QComboBox, QInputDialog, QMenu,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QProcess

from nmlinux.core.rdp import (
    RdpConnection, RdpGroup, RdpStore,
    build_rdp_args, find_xfreerdp, launch_rdp_macos, _IS_MACOS,
)
from nmlinux.core.i18n import tr

_EMPTY  = 0
_DETAIL = 1
_FORM   = 2


# ── RDP page ───────────────────────────────────────────────────────────────

class RdpPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._store = RdpStore()
        self._groups, self._connections = self._store.load()
        self._editing_id: str | None = None

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

        btn_new_conn = QPushButton(QIcon.fromTheme("list-add"), " " + tr("rdp_new_conn_btn"))
        btn_new_conn.clicked.connect(self._on_new)
        btn_new_grp  = QPushButton(QIcon.fromTheme("folder-new"), " " + tr("rdp_new_grp_btn"))
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
        return self._right

    def _build_empty(self) -> QWidget:
        w = QWidget()
        lbl = QLabel(tr("rdp_empty_state"))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: palette(mid); font-size: 14px;")
        QVBoxLayout(w).addWidget(lbl)
        return w

    def _build_detail(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._det_name       = QLabel()
        self._det_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._det_subtitle   = QLabel()
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
        for key, lbl_key in [
            ("host",       "rdp_det_lbl_host"),
            ("port",       "rdp_det_lbl_port"),
            ("username",   "rdp_det_lbl_user"),
            ("domain",     "rdp_det_lbl_domain"),
            ("resolution", "rdp_det_lbl_resolution"),
            ("fullscreen", "rdp_det_lbl_fullscreen"),
            ("notes",      "rdp_det_lbl_notes"),
        ]:
            val = QLabel()
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setWordWrap(True)
            self._det[key] = val
            form.addRow(tr(lbl_key) + " :", val)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        self._btn_connect = QPushButton(QIcon.fromTheme("network-connect"), " " + tr("rdp_connect_btn"))
        self._btn_connect.setDefault(True)
        self._btn_connect.clicked.connect(self._on_connect)
        btn_edit = QPushButton(QIcon.fromTheme("document-edit"), " " + tr("rdp_edit_btn"))
        btn_edit.clicked.connect(self._on_edit)
        btn_del  = QPushButton(QIcon.fromTheme("edit-delete"), " " + tr("rdp_delete_btn"))
        btn_del.clicked.connect(self._on_delete)
        row.addWidget(self._btn_connect)
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

        self._f_name       = QLineEdit(); self._f_name.setPlaceholderText(tr("rdp_form_name_ph"))
        self._f_group      = QComboBox()
        self._f_host       = QLineEdit(); self._f_host.setPlaceholderText("192.168.1.100")
        self._f_port       = QSpinBox();  self._f_port.setRange(1, 65535); self._f_port.setValue(3389)
        self._f_user       = QLineEdit(); self._f_user.setPlaceholderText(tr("rdp_form_user_ph"))
        self._f_domain     = QLineEdit(); self._f_domain.setPlaceholderText(tr("rdp_form_domain_ph"))
        self._f_resolution = QComboBox()
        for res in ["1920x1080", "1280x720", "1600x900", "2560x1440", "3840x2160"]:
            self._f_resolution.addItem(res)
        self._f_resolution.setEditable(True)
        self._f_fullscreen = QCheckBox()
        self._f_notes      = QTextEdit(); self._f_notes.setMaximumHeight(80)

        form.addRow(tr("rdp_form_lbl_name"),       self._f_name)
        form.addRow(tr("rdp_form_lbl_group"),       self._f_group)
        form.addRow(tr("rdp_form_lbl_host"),        self._f_host)
        form.addRow(tr("rdp_form_lbl_port"),        self._f_port)
        form.addRow(tr("rdp_form_lbl_user"),        self._f_user)
        form.addRow(tr("rdp_form_lbl_domain"),      self._f_domain)
        form.addRow(tr("rdp_form_lbl_resolution"),  self._f_resolution)
        form.addRow(tr("rdp_form_lbl_fullscreen"),  self._f_fullscreen)
        form.addRow(tr("rdp_form_lbl_notes"),       self._f_notes)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        btn_save   = QPushButton(QIcon.fromTheme("document-save"), " " + tr("rdp_save_btn"))
        btn_save.setDefault(True); btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton(QIcon.fromTheme("dialog-cancel"), " " + tr("rdp_cancel_btn"))
        btn_cancel.clicked.connect(self._on_cancel)
        row.addWidget(btn_save); row.addWidget(btn_cancel); row.addStretch(1)
        layout.addLayout(row)
        return w

    # ── Tree helpers ───────────────────────────────────────────────────────

    def _group_path(self, group_id: str) -> str:
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
        for group in self._groups:
            if group.parent_id == parent_group_id:
                g_item = QTreeWidgetItem(parent_item, [group.name])
                g_item.setIcon(0, icon_grp)
                g_item.setData(0, Qt.ItemDataRole.UserRole, ('group', group.id))
                g_item.setExpanded(True)
                f = g_item.font(0); f.setBold(True); g_item.setFont(0, f)
                self._build_tree_children(g_item, group.id, icon_conn, icon_grp)
        for conn in self._connections:
            if conn.group_id == parent_group_id:
                c_item = QTreeWidgetItem(parent_item, [conn.display_name])
                c_item.setIcon(0, icon_conn)
                c_item.setToolTip(0, conn.subtitle)
                c_item.setData(0, Qt.ItemDataRole.UserRole, ('conn', conn.id))

    def _refresh_list(self, select_conn_id: str | None = None) -> None:
        self._tree.blockSignals(True)
        self._tree.clear()
        icon_conn = QIcon.fromTheme("computer")
        icon_grp  = QIcon.fromTheme("folder")
        self._build_tree_children(self._tree.invisibleRootItem(), "", icon_conn, icon_grp)
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

    def _current_conn(self) -> RdpConnection | None:
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
        self._f_group.addItem(tr("rdp_no_group"), "")

        def add_group(grp: RdpGroup, indent: int) -> None:
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

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _prev) -> None:
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
                self._launch_rdp(conn)

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
            act_connect = menu.addAction(QIcon.fromTheme("network-connect"), tr("rdp_ctx_connect"))
            menu.addSeparator()
            act_edit = menu.addAction(QIcon.fromTheme("document-edit"), tr("rdp_ctx_edit"))
            act_del  = menu.addAction(QIcon.fromTheme("edit-delete"),   tr("rdp_ctx_delete"))
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_connect:
                self._launch_rdp(conn)
            elif act == act_edit:
                self._tree.setCurrentItem(item); self._on_edit()
            elif act == act_del:
                self._tree.setCurrentItem(item); self._on_delete()

        elif kind == 'group':
            grp = next((g for g in self._groups if g.id == item_id), None)
            if grp is None:
                return
            act_rename  = menu.addAction(QIcon.fromTheme("document-edit"), tr("rdp_ctx_rename_grp"))
            act_add_sub = menu.addAction(QIcon.fromTheme("folder-new"),    tr("rdp_ctx_add_sub"))
            menu.addSeparator()
            act_del = menu.addAction(QIcon.fromTheme("edit-delete"), tr("rdp_ctx_delete_grp"))
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_rename:
                self._rename_group(item_id)
            elif act == act_add_sub:
                self._new_subgroup(item_id)
            elif act == act_del:
                self._delete_group(item_id)

    # ── Slots — detail ─────────────────────────────────────────────────────

    def _show_detail(self, conn: RdpConnection) -> None:
        self._det_name.setText(conn.display_name)
        self._det_subtitle.setText(conn.subtitle)
        path = self._group_path(conn.group_id)
        self._det_group_path.setText(path)
        self._det_group_path.setVisible(bool(path))
        self._det["host"].setText(conn.host)
        self._det["port"].setText(str(conn.port))
        self._det["username"].setText(conn.username or "—")
        self._det["domain"].setText(conn.domain or "—")
        self._det["resolution"].setText(conn.resolution)
        self._det["fullscreen"].setText("✓" if conn.fullscreen else "—")
        self._det["notes"].setText(conn.notes or "")
        self._right.setCurrentIndex(_DETAIL)

    def _on_connect(self) -> None:
        conn = self._current_conn()
        if conn:
            self._launch_rdp(conn)

    def _on_edit(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        self._editing_id = conn.id
        self._form_title.setText(tr("rdp_form_title_edit"))
        self._populate_group_combo(conn.group_id)
        self._f_name.setText(conn.name)
        self._f_host.setText(conn.host)
        self._f_port.setValue(conn.port)
        self._f_user.setText(conn.username)
        self._f_domain.setText(conn.domain)
        idx = self._f_resolution.findText(conn.resolution)
        if idx >= 0:
            self._f_resolution.setCurrentIndex(idx)
        else:
            self._f_resolution.setCurrentText(conn.resolution)
        self._f_fullscreen.setChecked(conn.fullscreen)
        self._f_notes.setPlainText(conn.notes)
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_delete(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        ans = QMessageBox.question(
            self, tr("rdp_dlg_del_title"),
            tr("rdp_dlg_del_msg", name=conn.display_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        self._connections = [c for c in self._connections if c.id != conn.id]
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    # ── Slots — form ───────────────────────────────────────────────────────

    def _on_new(self) -> None:
        preselect = ""
        item = self._tree.currentItem()
        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'group':
                preselect = data[1]
        self._editing_id = None
        self._form_title.setText(tr("rdp_form_title_new"))
        self._populate_group_combo(preselect)
        self._f_name.clear()
        self._f_host.clear()
        self._f_port.setValue(3389)
        self._f_user.clear()
        self._f_domain.clear()
        self._f_resolution.setCurrentIndex(0)
        self._f_fullscreen.setChecked(False)
        self._f_notes.clear()
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_save(self) -> None:
        host = self._f_host.text().strip()
        if not host:
            QMessageBox.warning(self, tr("rdp_dlg_req_title"), tr("rdp_dlg_req_msg"))
            self._f_host.setFocus()
            return
        updated = RdpConnection(
            id         = self._editing_id or str(uuid.uuid4()),
            name       = self._f_name.text().strip() or host,
            host       = host,
            port       = self._f_port.value(),
            username   = self._f_user.text().strip(),
            domain     = self._f_domain.text().strip(),
            resolution = self._f_resolution.currentText().strip(),
            fullscreen = self._f_fullscreen.isChecked(),
            notes      = self._f_notes.toPlainText().strip(),
            group_id   = self._f_group.currentData() or "",
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

    # ── Slots — group management ───────────────────────────────────────────

    def _on_new_group(self) -> None:
        name, ok = QInputDialog.getText(self, tr("rdp_dlg_new_grp_title"), tr("rdp_dlg_new_grp_prompt"))
        if not ok or not name.strip():
            return
        top_groups = [g for g in self._groups if not g.parent_id]
        parent_id = ""
        if top_groups:
            choices = [tr("rdp_root_level")] + [g.name for g in top_groups]
            choice, ok2 = QInputDialog.getItem(
                self, tr("rdp_dlg_parent_title"), tr("rdp_dlg_parent_prompt"), choices, 0, False
            )
            if not ok2:
                return
            if choice != choices[0]:
                parent_id = top_groups[choices.index(choice) - 1].id
        self._groups.append(RdpGroup(name=name.strip(), parent_id=parent_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _new_subgroup(self, parent_group_id: str) -> None:
        parent = next((g for g in self._groups if g.id == parent_group_id), None)
        if parent is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("rdp_dlg_new_sub_title"),
            tr("rdp_dlg_new_sub_prompt", parent=parent.name)
        )
        if not ok or not name.strip():
            return
        self._groups.append(RdpGroup(name=name.strip(), parent_id=parent_group_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _rename_group(self, group_id: str) -> None:
        grp = next((g for g in self._groups if g.id == group_id), None)
        if grp is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("rdp_dlg_rename_title"), tr("rdp_dlg_rename_prompt"), text=grp.name
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
            self, tr("rdp_dlg_del_grp_title"),
            tr("rdp_dlg_del_grp_msg", name=grp.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
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

    # ── RDP launch ─────────────────────────────────────────────────────────

    def _launch_rdp(self, conn: RdpConnection) -> None:
        binary = find_xfreerdp()
        if binary is None:
            if _IS_MACOS:
                ok, err = launch_rdp_macos(conn)
                if not ok:
                    QMessageBox.warning(self, "RDP", err)
                return
            QMessageBox.warning(self, tr("rdp_missing_title"), tr("rdp_missing_msg"))
            return
        password, ok = QInputDialog.getText(
            self,
            conn.display_name,
            tr("rdp_password_prompt"),
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        args = build_rdp_args(conn, password, binary=binary)
        proc = QProcess(self)
        proc.startDetached(args[0], args[1:])
