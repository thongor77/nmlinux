from __future__ import annotations
import sys
import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QMenu

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    return app

from nmlinux.pages.asset_inventory import AssetInventoryPage, _COL_IP, _COL_OS, _COL_METHOD


def test_on_host_inserts_new_row(qapp):
    page = AssetInventoryPage()
    page._on_host({'ip': '10.0.0.5', 'hostname': 'nas', 'method': 'Nmap'})
    assert page._table.rowCount() == 1
    assert page._table.item(0, _COL_IP).text() == '10.0.0.5'


def test_on_host_updates_existing_row_instead_of_duplicating(qapp):
    page = AssetInventoryPage()
    page._on_host({'ip': '10.0.0.5', 'hostname': '', 'method': 'Nmap'})
    page._on_host({
        'ip': '10.0.0.5', 'hostname': 'mac-mini', 'os': 'macOS 15', 'method': 'SSH',
    })
    assert page._table.rowCount() == 1
    assert page._table.item(0, _COL_OS).text() == 'macOS 15'
    assert page._table.item(0, _COL_METHOD).text() == 'SSH'


def test_find_row_by_ip_returns_minus_one_when_absent(qapp):
    page = AssetInventoryPage()
    assert page._find_row_by_ip('10.0.0.9') == -1


def test_table_context_menu_policy_set(qapp):
    page = AssetInventoryPage()
    assert page._table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_selected_ips_returns_ips_for_all_selected_rows(qapp):
    page = AssetInventoryPage()
    page._on_host({'ip': '10.0.0.5', 'hostname': 'a', 'method': 'Nmap'})
    page._on_host({'ip': '10.0.0.6', 'hostname': 'b', 'method': 'Nmap'})
    page._table.selectAll()
    assert set(page._selected_ips()) == {'10.0.0.5', '10.0.0.6'}


def test_selected_ips_empty_when_nothing_selected(qapp):
    page = AssetInventoryPage()
    page._on_host({'ip': '10.0.0.5', 'hostname': 'a', 'method': 'Nmap'})
    page._table.clearSelection()
    assert page._selected_ips() == []


def _patch_menu_exec(monkeypatch, on_exec):
    """QMenu.exec is a C++-bound method; overriding it at the class level
    (monkeypatch.setattr(QMenu, 'exec', ...)) is silently ignored by PySide6,
    so the real modal exec() runs instead (harmlessly returning immediately
    under the offscreen test platform, but never invoking on_exec). Patching
    QMenu.__init__ to stamp an instance-level `exec` attribute on each menu
    as it's constructed does take effect, since that's a plain Python
    attribute lookup rather than a call into the C++ vtable.
    """
    orig_init = QMenu.__init__

    def fake_init(self, *a, **kw):
        orig_init(self, *a, **kw)
        self.exec = lambda pos=None: on_exec(self)

    monkeypatch.setattr(QMenu, '__init__', fake_init)


def test_context_menu_selects_row_under_cursor_if_not_selected(qapp, monkeypatch):
    page = AssetInventoryPage()
    page._on_host({'ip': '10.0.0.5', 'hostname': 'a', 'method': 'Nmap'})
    page._on_host({'ip': '10.0.0.6', 'hostname': 'b', 'method': 'Nmap'})
    page._table.selectRow(0)
    monkeypatch.setattr(page._table, 'rowAt', lambda y: 1)
    _patch_menu_exec(monkeypatch, on_exec=lambda menu: None)

    page._on_table_context_menu(QPoint(0, 0))

    selected = {idx.row() for idx in page._table.selectionModel().selectedRows()}
    assert selected == {1}


def test_context_menu_noop_when_clicking_empty_area(qapp, monkeypatch):
    page = AssetInventoryPage()
    monkeypatch.setattr(page._table, 'rowAt', lambda y: -1)
    exec_called = []
    _patch_menu_exec(monkeypatch, on_exec=lambda menu: exec_called.append(True))

    page._on_table_context_menu(QPoint(0, 0))

    assert exec_called == []


def test_context_menu_refresh_action_rescans_selected_hosts(qapp, monkeypatch):
    page = AssetInventoryPage()
    page._on_host({'ip': '10.0.0.5', 'hostname': 'a', 'method': 'Nmap'})
    page._on_host({'ip': '10.0.0.6', 'hostname': 'b', 'method': 'Nmap'})
    page._table.selectAll()
    monkeypatch.setattr(page._table, 'rowAt', lambda y: 0)
    _patch_menu_exec(monkeypatch, on_exec=lambda menu: menu.actions()[0].trigger())

    calls = []
    monkeypatch.setattr(page, '_start_scan', lambda ips, clear: calls.append((set(ips), clear)))

    page._on_table_context_menu(QPoint(0, 0))

    assert calls == [({'10.0.0.5', '10.0.0.6'}, False)]
