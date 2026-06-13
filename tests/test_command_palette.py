from nmlinux.command_palette import filter_modules, _KEYWORDS

_LABELS = [
    "Dashboard", "Connections", "Interfaces", "Wi-Fi", "Subnet",
    "DNS", "Ping", "IP Scanner", "Port Scanner", "Nmap", "Whois",
    "TLS Inspector", "SMB / NFS", "Hosts File", "SNMP", "SNTP / NTP",
    "SSH", "SSH Keys", "Remote Desktop", "VNC", "Traceroute", "MTR",
    "Firewall", "Speed Test", "Bandwidth", "Wake on LAN", "Topology",
]


def test_empty_query_returns_all():
    results = filter_modules("", _LABELS)
    assert len(results) == 27
    assert results[0] == (0, "Dashboard")


def test_exact_label_match():
    results = filter_modules("SSH", _LABELS)
    labels = [label for _, label in results]
    assert "SSH" in labels


def test_partial_label_match():
    results = filter_modules("dash", _LABELS)
    assert (0, "Dashboard") in results


def test_keyword_match_wifi():
    results = filter_modules("wireless", _LABELS)
    assert (3, "Wi-Fi") in results


def test_keyword_match_firewall():
    results = filter_modules("iptables", _LABELS)
    assert (22, "Firewall") in results


def test_keyword_match_rdp():
    results = filter_modules("rdp", _LABELS)
    assert (18, "Remote Desktop") in results


def test_no_match_returns_empty():
    results = filter_modules("xyzzy_no_match", _LABELS)
    assert results == []


def test_case_insensitive_label():
    results = filter_modules("TOPOLOGY", _LABELS)
    assert (26, "Topology") in results


def test_case_insensitive_keyword():
    results = filter_modules("TERMINAL", _LABELS)
    labels = [label for _, label in results]
    assert "SSH" in labels


def test_all_labels_have_keywords():
    for label in _LABELS:
        assert label in _KEYWORDS, f"Missing keyword entry for: {label}"
        assert len(_KEYWORDS[label]) > 0, f"Empty keywords for: {label}"
