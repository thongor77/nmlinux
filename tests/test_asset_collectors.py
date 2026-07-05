from __future__ import annotations

from nmlinux.core import asset_collectors as ac


# ── _is_alive retry behaviour ───────────────────────────────────────────────

def test_is_alive_retries_ping_before_falling_back(monkeypatch):
    """A single dropped ICMP reply must not immediately mark a host dead."""
    calls = []

    def fake_ping(ip, timeout=1):
        calls.append(ip)
        return len(calls) >= 2  # first attempt drops, second succeeds

    monkeypatch.setattr(ac, '_ping', fake_ping)
    monkeypatch.setattr(ac, '_port_open', lambda ip, p, timeout=1.0: False)

    assert ac._is_alive('10.0.0.5') is True
    assert len(calls) == 2


def test_is_alive_falls_back_to_port_probe_after_ping_exhausted(monkeypatch):
    monkeypatch.setattr(ac, '_ping', lambda ip, timeout=1: False)
    monkeypatch.setattr(ac, '_port_open', lambda ip, p, timeout=1.0: p == 445)

    assert ac._is_alive('10.0.0.5') is True


def test_is_alive_false_when_ping_and_ports_all_fail(monkeypatch):
    monkeypatch.setattr(ac, '_ping', lambda ip, timeout=1: False)
    monkeypatch.setattr(ac, '_port_open', lambda ip, p, timeout=1.0: False)

    assert ac._is_alive('10.0.0.5') is False


# ── missing_ips helper (drives the "refresh empty" button) ─────────────────

def test_missing_ips_returns_attempted_minus_found():
    attempted = ['10.0.0.1', '10.0.0.2', '10.0.0.3']
    found = {'10.0.0.1'}
    assert ac.missing_ips(attempted, found) == ['10.0.0.2', '10.0.0.3']


def test_missing_ips_empty_when_all_found():
    attempted = ['10.0.0.1', '10.0.0.2']
    found = {'10.0.0.1', '10.0.0.2'}
    assert ac.missing_ips(attempted, found) == []


def test_missing_ips_preserves_attempted_order():
    attempted = ['10.0.0.3', '10.0.0.1', '10.0.0.2']
    found = {'10.0.0.1'}
    assert ac.missing_ips(attempted, found) == ['10.0.0.3', '10.0.0.2']


# ── _collect_ssh auth-failure feedback ──────────────────────────────────────

def test_collect_ssh_returns_error_when_creds_rejected(monkeypatch):
    monkeypatch.setattr(ac, '_ssh_connects', lambda ip, creds, timeout: False)
    creds = [{'user': 'admin', 'password': 'wrong'}]
    assert ac._collect_ssh('10.0.0.5', creds, 5) == {'ssh_error': 'SSH auth failed'}


def test_collect_ssh_returns_empty_when_no_creds_configured(monkeypatch):
    monkeypatch.setattr(ac, '_ssh_connects', lambda ip, creds, timeout: False)
    assert ac._collect_ssh('10.0.0.5', [{}], 5) == {}


def test_collect_ssh_succeeds_returns_collected_data(monkeypatch):
    monkeypatch.setattr(ac, '_ssh_connects', lambda ip, creds, timeout: True)
    monkeypatch.setattr(
        ac, '_do_collect_ssh',
        lambda ip, creds, timeout: {'method': 'SSH', 'os': 'Ubuntu'},
    )
    creds = [{'user': 'admin', 'password': 'right'}]
    assert ac._collect_ssh('10.0.0.5', creds, 5) == {'method': 'SSH', 'os': 'Ubuntu'}


# ── collect_host keeps Nmap data when SSH auth fails ────────────────────────

def test_collect_host_keeps_nmap_data_when_ssh_auth_fails(monkeypatch):
    monkeypatch.setattr(ac, '_is_alive', lambda ip, timeout=1: True)
    monkeypatch.setattr(ac, '_nmap_detect', lambda ip, timeout=5: {
        'ip': ip, 'hostname': 'nas.local', 'platform': 'Linux', 'os': '', 'method': 'Nmap',
    })
    monkeypatch.setattr(ac, '_port_open', lambda ip, port, timeout=1.5: port == 22)
    monkeypatch.setattr(
        ac, '_collect_ssh',
        lambda ip, creds, timeout: {'ssh_error': 'SSH auth failed'},
    )

    result = ac.collect_host('10.0.0.5', [{'user': 'admin', 'password': 'wrong'}], [], {})

    assert result['method'] == 'Nmap'
    assert result['hostname'] == 'nas.local'
    assert result['ssh_error'] == 'SSH auth failed'
