from __future__ import annotations
import sys
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    return app

from nmlinux.core.host_actions import (
    HostActionMenu,
    ACT_PING, ACT_PORT_SCAN, ACT_WHOIS, ACT_DNS,
    ACT_TRACEROUTE, ACT_MTR, ACT_SSH, ACT_RDP,
    ACT_VNC, ACT_TOPOLOGY, ACT_ASSET,
)

def test_all_actions_present(qapp):
    menu = HostActionMenu("1.2.3.4")
    keys = set()
    menu.action_chosen.connect(lambda k, ip, h: keys.add(k))
    for action in menu.actions():
        if not action.isSeparator():
            action.trigger()
    assert keys == {ACT_PING, ACT_PORT_SCAN, ACT_WHOIS, ACT_DNS,
                    ACT_TRACEROUTE, ACT_MTR, ACT_SSH, ACT_RDP,
                    ACT_VNC, ACT_TOPOLOGY, ACT_ASSET}

def test_signal_carries_ip_and_host(qapp):
    received = []
    menu = HostActionMenu("10.0.0.1", "myhost")
    menu.action_chosen.connect(lambda k, ip, h: received.append((ip, h)))
    for action in menu.actions():
        if ACT_PING in action.text().lower() or "ping" in action.text().lower():
            action.trigger()
            break
    assert received and received[0] == ("10.0.0.1", "myhost")

def test_bold_when_port_detected(qapp):
    menu = HostActionMenu("1.2.3.4", ports=[22, 3389])
    bold_labels = {a.text() for a in menu.actions() if not a.isSeparator() and a.font().bold()}
    assert "SSH" in bold_labels
    assert "RDP" in bold_labels
    assert "VNC" not in bold_labels

def test_no_bold_without_ports(qapp):
    menu = HostActionMenu("1.2.3.4")
    bold_labels = {a.text() for a in menu.actions() if not a.isSeparator() and a.font().bold()}
    assert not bold_labels
