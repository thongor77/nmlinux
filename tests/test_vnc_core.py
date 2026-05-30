from __future__ import annotations
import json
from pathlib import Path
from nmlinux.core.vnc import (
    VncGroup, VncConnection, VncStore, build_vnc_args
)


# ── build_vnc_args ─────────────────────────────────────────────────────────

def test_args_basic():
    conn = VncConnection(host="192.168.1.20", port=5900)
    args = build_vnc_args(conn, "vncviewer")
    assert args[0] == "vncviewer"
    assert "-autopass" not in args
    assert "-passwd" not in args
    assert "192.168.1.20::5900" in args

def test_args_with_username():
    conn = VncConnection(host="192.168.1.20", port=5900, username="luust")
    args = build_vnc_args(conn, "vncviewer")
    assert "-username" in args
    assert "luust" in args

def test_args_no_username():
    conn = VncConnection(host="192.168.1.20", port=5900, username="")
    args = build_vnc_args(conn, "vncviewer")
    assert "-username" not in args

def test_args_custom_binary():
    conn = VncConnection(host="srv", port=5901)
    args = build_vnc_args(conn, "tigervnc")
    assert args[0] == "tigervnc"

def test_args_port_format():
    conn = VncConnection(host="myhost", port=5902)
    args = build_vnc_args(conn, "vncviewer")
    assert "myhost::5902" in args


# ── VncConnection defaults ─────────────────────────────────────────────────

def test_connection_defaults():
    conn = VncConnection()
    assert conn.port == 5900
    assert conn.username == ""
    assert conn.group_id == ""

def test_display_name_uses_name():
    conn = VncConnection(name="MacBook", host="192.168.1.20")
    assert conn.display_name == "MacBook"

def test_display_name_falls_back_to_host():
    conn = VncConnection(name="", host="192.168.1.20")
    assert conn.display_name == "192.168.1.20"

def test_subtitle_with_username():
    conn = VncConnection(host="srv", username="luust", port=5900)
    assert "luust" in conn.subtitle
    assert "srv" in conn.subtitle

def test_subtitle_default_port_omitted():
    conn = VncConnection(host="srv", port=5900)
    sub = conn.subtitle
    assert "5900" not in sub

def test_subtitle_nondefault_port_shown():
    conn = VncConnection(host="srv", port=5901)
    assert "5901" in conn.subtitle


# ── VncStore ───────────────────────────────────────────────────────────────

def test_store_roundtrip(tmp_path):
    path = tmp_path / "vnc.json"
    store = VncStore(path)
    groups = [VncGroup(name="macOS"), VncGroup(name="Linux")]
    conns = [
        VncConnection(name="MacBook", host="192.168.1.20", username="luust"),
        VncConnection(name="Plex", host="192.168.1.30"),
    ]
    store.save(groups, conns)
    lg, lc = store.load()
    assert len(lg) == 2
    assert len(lc) == 2
    assert lc[0].username == "luust"

def test_store_load_missing_file(tmp_path):
    store = VncStore(tmp_path / "missing.json")
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_load_corrupt_file(tmp_path):
    path = tmp_path / "vnc.json"
    path.write_text("not json")
    store = VncStore(path)
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_json_format(tmp_path):
    path = tmp_path / "vnc.json"
    store = VncStore(path)
    store.save([VncGroup(name="G")], [VncConnection(name="C", host="h")])
    raw = json.loads(path.read_text())
    assert raw["version"] == 2
    assert "groups" in raw
    assert "connections" in raw
