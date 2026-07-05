from __future__ import annotations
import sys
import pytest
from PySide6.QtWidgets import QApplication

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
