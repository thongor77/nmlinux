from __future__ import annotations
import json
from pathlib import Path
import pytest
from nmlinux.core.rdp import (
    RdpGroup, RdpConnection, RdpStore, build_rdp_args
)


# ── build_rdp_args ─────────────────────────────────────────────────────────

def test_args_basic():
    conn = RdpConnection(host="192.168.1.10", username="admin", port=3389)
    args = build_rdp_args(conn, "secret")
    assert "/v:192.168.1.10:3389" in args
    assert "/u:admin" in args
    assert "/p:secret" in args
    assert "/cert:ignore" in args
    assert "/dynamic-resolution" in args

def test_args_no_domain():
    conn = RdpConnection(host="srv", username="user", domain="")
    args = build_rdp_args(conn, "pw")
    assert not any(a.startswith("/d:") for a in args)

def test_args_with_domain():
    conn = RdpConnection(host="srv", username="user", domain="CORP")
    args = build_rdp_args(conn, "pw")
    assert "/d:CORP" in args

def test_args_resolution():
    conn = RdpConnection(host="srv", resolution="1920x1080", fullscreen=False)
    args = build_rdp_args(conn, "pw")
    assert "/size:1920x1080" in args
    assert "/f" not in args

def test_args_fullscreen():
    conn = RdpConnection(host="srv", fullscreen=True)
    args = build_rdp_args(conn, "pw")
    assert "/f" in args
    assert not any(a.startswith("/size:") for a in args)

def test_args_first_element_is_xfreerdp():
    conn = RdpConnection(host="srv")
    args = build_rdp_args(conn, "pw")
    assert args[0] == "xfreerdp"


# ── RdpConnection defaults ─────────────────────────────────────────────────

def test_connection_defaults():
    conn = RdpConnection()
    assert conn.port == 3389
    assert conn.resolution == "1920x1080"
    assert conn.fullscreen is False
    assert conn.domain == ""
    assert conn.group_id == ""

def test_display_name_uses_name():
    conn = RdpConnection(name="Mon PC", host="192.168.1.5")
    assert conn.display_name == "Mon PC"

def test_display_name_falls_back_to_host():
    conn = RdpConnection(name="", host="192.168.1.5")
    assert conn.display_name == "192.168.1.5"

def test_subtitle_includes_user_and_host():
    conn = RdpConnection(host="srv", username="admin", port=3389)
    assert "admin" in conn.subtitle
    assert "srv" in conn.subtitle


# ── RdpStore ───────────────────────────────────────────────────────────────

def test_store_roundtrip(tmp_path):
    path = tmp_path / "rdp.json"
    store = RdpStore(path)
    groups = [RdpGroup(name="Boulot"), RdpGroup(name="Perso")]
    conns  = [
        RdpConnection(name="AD", host="10.0.0.1", username="admin", domain="CORP"),
        RdpConnection(name="NAS", host="10.0.0.2"),
    ]
    store.save(groups, conns)
    loaded_groups, loaded_conns = store.load()
    assert len(loaded_groups) == 2
    assert len(loaded_conns) == 2
    assert loaded_conns[0].host == "10.0.0.1"
    assert loaded_conns[0].domain == "CORP"

def test_store_load_missing_file(tmp_path):
    store = RdpStore(tmp_path / "missing.json")
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_load_corrupt_file(tmp_path):
    path = tmp_path / "rdp.json"
    path.write_text("not json")
    store = RdpStore(path)
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_json_format(tmp_path):
    path = tmp_path / "rdp.json"
    store = RdpStore(path)
    store.save([RdpGroup(name="G")], [RdpConnection(name="C", host="h")])
    raw = json.loads(path.read_text())
    assert raw["version"] == 2
    assert "groups" in raw
    assert "connections" in raw
