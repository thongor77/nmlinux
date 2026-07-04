from __future__ import annotations

from nmlinux.pages.ping import PingTarget, _PingTargetStore


def test_store_starts_empty_when_file_missing(tmp_path):
    store = _PingTargetStore(tmp_path / 'missing.json')
    assert store.all() == []


def test_add_persists_and_reloads(tmp_path):
    path = tmp_path / 'targets.json'
    store = _PingTargetStore(path)
    store.add(PingTarget(name='Spain DNS', host='8.8.8.8', interval=5))

    reloaded = _PingTargetStore(path)
    assert reloaded.all() == [PingTarget(name='Spain DNS', host='8.8.8.8', interval=5)]


def test_update_replaces_entry_at_index(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    store.add(PingTarget(name='A', host='1.1.1.1'))
    store.update(0, PingTarget(name='B', host='2.2.2.2'))
    assert store.all() == [PingTarget(name='B', host='2.2.2.2')]


def test_remove_deletes_entry_at_index(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    store.add(PingTarget(name='A', host='1.1.1.1'))
    store.add(PingTarget(name='B', host='2.2.2.2'))
    store.remove(0)
    assert store.all() == [PingTarget(name='B', host='2.2.2.2')]


def test_load_corrupt_json_returns_empty_list(tmp_path):
    path = tmp_path / 'targets.json'
    path.write_text('not valid json {')
    store = _PingTargetStore(path)
    assert store.all() == []


def test_has_host_true_when_present(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    store.add(PingTarget(name='A', host='1.1.1.1'))
    assert store.has_host('1.1.1.1') is True


def test_has_host_false_when_absent(tmp_path):
    store = _PingTargetStore(tmp_path / 'targets.json')
    assert store.has_host('1.1.1.1') is False
