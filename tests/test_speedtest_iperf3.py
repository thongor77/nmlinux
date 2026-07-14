from __future__ import annotations

import json

from nmlinux.pages.speedtest import (
    Iperf3Server,
    Iperf3Worker,
    _Iperf3ServerStore,
    _IPERF3_PUBLIC_SERVERS_PATH,
    _load_public_servers,
)


# ── _Iperf3ServerStore persistence ──────────────────────────────────────────

def test_store_starts_empty_when_file_missing(tmp_path):
    store = _Iperf3ServerStore(tmp_path / 'missing.json')
    assert store.all() == []


def test_add_persists_and_reloads(tmp_path):
    path = tmp_path / 'servers.json'
    store = _Iperf3ServerStore(path)
    store.add(Iperf3Server(name='Home lab', host='10.0.0.5', port=5201))

    reloaded = _Iperf3ServerStore(path)
    assert reloaded.all() == [Iperf3Server(name='Home lab', host='10.0.0.5', port=5201)]


def test_remove_deletes_entry_at_index(tmp_path):
    store = _Iperf3ServerStore(tmp_path / 'servers.json')
    store.add(Iperf3Server(name='A', host='1.1.1.1', port=5201))
    store.add(Iperf3Server(name='B', host='2.2.2.2', port=5202))
    store.remove(0)
    assert store.all() == [Iperf3Server(name='B', host='2.2.2.2', port=5202)]


def test_load_corrupt_json_returns_empty_list(tmp_path):
    path = tmp_path / 'servers.json'
    path.write_text('not valid json {')
    store = _Iperf3ServerStore(path)
    assert store.all() == []


def test_load_ignores_unknown_fields(tmp_path):
    path = tmp_path / 'servers.json'
    path.write_text(json.dumps([
        {'name': 'A', 'host': '1.1.1.1', 'port': 5201, 'stray_field': 'x'},
    ]))
    store = _Iperf3ServerStore(path)
    assert store.all() == [Iperf3Server(name='A', host='1.1.1.1', port=5201)]


# ── Bundled public server list ──────────────────────────────────────────────

def test_bundled_public_servers_file_exists():
    assert _IPERF3_PUBLIC_SERVERS_PATH.exists()


def test_load_public_servers_returns_entries_with_required_fields():
    servers = _load_public_servers()
    assert len(servers) > 0
    for entry in servers:
        assert isinstance(entry.get('country'), str) and entry['country']
        assert isinstance(entry.get('name'), str) and entry['name']
        assert isinstance(entry.get('host'), str) and entry['host']
        assert isinstance(entry.get('port'), int)


def test_load_public_servers_missing_file_returns_empty(monkeypatch, tmp_path):
    import nmlinux.pages.speedtest as speedtest_mod
    monkeypatch.setattr(speedtest_mod, '_IPERF3_PUBLIC_SERVERS_PATH', tmp_path / 'missing.json')
    assert speedtest_mod._load_public_servers() == []


# ── Iperf3Worker JSON parsing ───────────────────────────────────────────────

def _tcp_worker() -> Iperf3Worker:
    return Iperf3Worker('host', 5201, udp=False, ip_mode='auto', reverse=False, duration=10)


def _udp_worker() -> Iperf3Worker:
    return Iperf3Worker('host', 5201, udp=True, ip_mode='auto', reverse=False, duration=10)


def test_parse_tcp_result():
    data = {
        "end": {
            "sum_sent":     {"bits_per_second": 941000000.0, "retransmits": 0},
            "sum_received": {"bits_per_second": 938000000.0},
        }
    }
    result = _tcp_worker()._parse(data)
    assert result['sent_mbps'] == 941.0
    assert result['received_mbps'] == 938.0
    assert result['jitter_ms'] is None
    assert result['loss_pct'] is None


def test_parse_udp_result():
    data = {
        "end": {
            "sum": {
                "bits_per_second": 1050000.0,
                "jitter_ms": 0.314,
                "lost_percent": 0.02,
            }
        }
    }
    result = _udp_worker()._parse(data)
    assert result['sent_mbps'] == 1.05
    assert result['received_mbps'] == 1.05
    assert result['jitter_ms'] == 0.314
    assert result['loss_pct'] == 0.02


def test_parse_tcp_missing_sections_defaults_to_zero():
    result = _tcp_worker()._parse({"end": {}})
    assert result['sent_mbps'] == 0.0
    assert result['received_mbps'] == 0.0
