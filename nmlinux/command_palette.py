from __future__ import annotations
from typing import Callable

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt

_KEYWORDS: dict[str, list[str]] = {
    "Dashboard":      ["home", "overview", "status", "summary"],
    "Connections":    ["connection", "manager", "nmcli", "network", "profile"],
    "Interfaces":     ["interface", "ip", "eth", "link", "adapter", "nic", "ifconfig"],
    "Wi-Fi":          ["wifi", "wireless", "wlan", "signal", "ssid", "wpa"],
    "Subnet":         ["subnet", "mask", "cidr", "network", "calculator", "netmask"],
    "DNS":            ["dns", "resolver", "nameserver", "lookup", "resolve"],
    "Ping":           ["ping", "icmp", "latency", "reachability", "echo"],
    "IP Scanner":     ["scan", "arp", "discovery", "hosts", "lan", "devices"],
    "Port Scanner":   ["port", "tcp", "udp", "open", "closed", "service"],
    "Nmap":           ["nmap", "scan", "security", "vulnerability", "probe"],
    "Whois":          ["whois", "domain", "registrar", "info", "lookup"],
    "TLS Inspector":  ["tls", "ssl", "certificate", "https", "security", "cert"],
    "SMB / NFS":      ["smb", "nfs", "samba", "shares", "windows", "mount"],
    "Hosts File":     ["hosts", "hostname", "etc", "local", "dns", "override"],
    "SNMP":           ["snmp", "monitoring", "oid", "trap", "agent"],
    "SNTP / NTP":     ["sntp", "ntp", "time", "sync", "clock", "date"],
    "SSH":            ["ssh", "remote", "terminal", "shell", "connect", "secure"],
    "SSH Keys":       ["ssh keys", "keygen", "ed25519", "rsa", "authorized", "public key"],
    "Remote Desktop": ["rdp", "remote desktop", "windows", "xfreerdp", "mstsc"],
    "VNC":            ["vnc", "remote", "display", "tigervnc", "desktop", "screen"],
    "Traceroute":     ["traceroute", "route", "hops", "path", "trace", "ttl"],
    "MTR":            ["mtr", "traceroute", "latency", "packet loss", "network", "path"],
    "Firewall":       ["firewall", "iptables", "nftables", "ufw", "rules", "block"],
    "Speed Test":     ["speed", "bandwidth", "download", "upload", "iperf", "throughput"],
    "Bandwidth":      ["bandwidth", "monitor", "rx", "tx", "traffic", "usage"],
    "Wake on LAN":    ["wol", "wake on lan", "magic packet", "boot", "remote", "power"],
    "Topology":       ["topology", "map", "network", "devices", "graph", "visual"],
}


def filter_modules(query: str, module_labels: list[str]) -> list[tuple[int, str]]:
    """Return (index, label) pairs matching query against labels and keywords.
    Empty query returns all modules."""
    q = query.lower().strip()
    if not q:
        return [(i, label) for i, label in enumerate(module_labels)]
    results = []
    for i, label in enumerate(module_labels):
        keywords = _KEYWORDS.get(label, [])
        if q in label.lower() or any(q in kw for kw in keywords):
            results.append((i, label))
    return results
