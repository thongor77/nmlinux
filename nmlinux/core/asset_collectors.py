from __future__ import annotations

import ipaddress
import platform
import shutil
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtCore import QThread, Signal

_IS_MACOS    = platform.system() == 'Darwin'

# .app bundles on macOS don't inherit the Homebrew PATH — probe known locations
_EXTRA_PATH  = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin'

def _which(cmd: str) -> str | None:
    return shutil.which(cmd) or shutil.which(cmd, path=_EXTRA_PATH)

_CMD_SSHPASS = _which('sshpass')
_CMD_SNMPGET = _which('snmpget')
_CMD_NMAP    = _which('nmap')

try:
    import winrm as _winrm
    _HAS_WINRM = True
except ImportError:
    _HAS_WINRM = False


# ── Nmap passive detection ────────────────────────────────────────────────────

def _nmap_detect(ip: str, timeout: int = 5) -> dict:
    result = {'ip': ip, 'hostname': '', 'platform': '?', 'os': '', 'method': 'Nmap'}
    try:
        result['hostname'] = socket.gethostbyaddr(ip)[0]
    except Exception:
        pass
    if not _CMD_NMAP:
        return result
    try:
        r = subprocess.run(
            [_CMD_NMAP, '-O', '--osscan-guess', '-T4', '--host-timeout', f'{timeout}s', '-n', ip],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        for line in r.stdout.splitlines():
            if 'OS details:' in line or 'Aggressive OS guesses:' in line:
                result['os'] = line.split(':', 1)[1].strip().split(',')[0][:60]
            if 'Running:' in line:
                val = line.split(':', 1)[1].strip().lower()
                if 'windows' in val:
                    result['platform'] = 'Windows'
                elif 'linux' in val:
                    result['platform'] = 'Linux'
                elif 'darwin' in val or 'mac os' in val or 'ios' in val:
                    result['platform'] = 'macOS'
                elif any(x in val for x in ('cisco', 'juniper', 'mikrotik', 'fortinet', 'ubiquiti')):
                    result['platform'] = 'Network'
    except Exception:
        pass
    return result


# ── SSH collection ────────────────────────────────────────────────────────────

def _ssh_run(ip: str, cmd: str, user: str, password: str, key: str, timeout: int) -> str:
    base = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=5',
        '-o', f'BatchMode={"yes" if not password else "no"}',
        '-o', 'LogLevel=ERROR',
    ]
    if key:
        base += ['-i', key]
    target = f'{user}@{ip}' if user else ip
    if password and _CMD_SSHPASS:
        cmd_list = [_CMD_SSHPASS, '-p', password] + base + [target, cmd]
    else:
        cmd_list = base + [target, cmd]
    try:
        r = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ''


def _ssh_connects(ip: str, creds: dict, timeout: int) -> bool:
    """Test SSH connectivity with a cheap echo command."""
    out = _ssh_run(ip, 'echo __nmlinux_ok__',
                   creds['user'], creds.get('password', ''), creds.get('key', ''),
                   min(timeout, 4))
    return '__nmlinux_ok__' in out


def _do_collect_ssh(ip: str, creds: dict, timeout: int) -> dict:
    user     = creds['user']
    password = creds.get('password', '')
    key      = creds.get('key', '')

    def run(cmd: str) -> str:
        return _ssh_run(ip, cmd, user, password, key, timeout)

    data: dict = {'method': 'SSH'}

    raw_os = run('uname -s 2>/dev/null || echo Unknown')
    is_macos = 'Darwin' in raw_os

    if is_macos:
        data['platform'] = 'macOS'
        # OS: sw_vers gives ProductName + ProductVersion on two lines
        data['os'] = run(
            "sw_vers 2>/dev/null | awk '/ProductName/{n=$NF} /ProductVersion/{v=$NF}"
            " END{if(n)print n,v}'"
        )[:80]
        # CPU: Intel has brand_string; Apple Silicon falls back to hw.model
        cpu_raw = run(
            'sysctl -n machdep.cpu.brand_string 2>/dev/null || sysctl -n hw.model 2>/dev/null'
        ).strip()
        cores = run('sysctl -n hw.logicalcpu 2>/dev/null').strip()
        # Disk: /System/Volumes/Data is the user-data volume on APFS (Ventura+)
        disk_line = run(
            '{ test -d /System/Volumes/Data && df -h /System/Volumes/Data | tail -1; } || df -h / | tail -1'
        ).strip()
        # RAM: macOS sysctl returns bytes
        hw = run('sysctl -n hw.memsize 2>/dev/null').strip()
        if hw.isdigit():
            data['ram'] = f'{int(hw) / (1024 ** 3):.1f} GB'
    else:
        if raw_os and raw_os != 'Unknown':
            data['platform'] = 'Linux'
        # OS: strip quotes from lsb_release output; use /etc/os-release as fallback
        data['os'] = run(
            r'lsb_release -ds 2>/dev/null | tr -d "\"" || '
            r'{ test -f /etc/os-release && grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d "\""; } || '
            'uname -r'
        )[:80]
        cpu_raw = run(
            'grep "model name" /proc/cpuinfo 2>/dev/null | head -1 | cut -d: -f2'
        ).strip()
        cores = run(
            'nproc 2>/dev/null || grep -c "^processor" /proc/cpuinfo 2>/dev/null'
        ).strip()
        # Disk: test -d avoids false-success from tail on empty df output
        disk_line = run(
            '{ test -d /mnt/user && df -h /mnt/user | tail -1; } || '
            '{ test -d /mnt/disk1 && df -h /mnt/disk1 | tail -1; } || '
            '{ test -d /volume1 && df -h /volume1 | tail -1; } || '
            'df -h / | tail -1'
        ).strip()
        # RAM: raw KB (Linux/BusyBox)
        ram_kb = run("free 2>/dev/null | grep '^Mem:' | awk '{print $2}'").strip()
        if ram_kb.isdigit():
            gb = int(ram_kb) / (1024 * 1024)
            data['ram'] = f'{gb:.1f} GB' if gb >= 1 else f'{int(ram_kb) // 1024} MB'

    data['cpu'] = f'{cpu_raw[:40]} ({cores}c)' if cpu_raw else ''

    if disk_line:
        parts = disk_line.split()
        if len(parts) >= 4:
            data['disk'] = f'{parts[1]} total, {parts[3]} free'

    data['uptime'] = run('uptime -p 2>/dev/null || uptime').strip()[:60]

    return {k: v for k, v in data.items() if v}


def _collect_ssh(ip: str, creds_list: list[dict], timeout: int) -> dict:
    """Try each credential set in order; return data from the first that connects."""
    for creds in creds_list:
        if not creds.get('user'):
            continue
        if _ssh_connects(ip, creds, timeout):
            return _do_collect_ssh(ip, creds, timeout)
    return {}


# ── WinRM collection ──────────────────────────────────────────────────────────

def _try_winrm(ip: str, creds: dict, timeout: int) -> dict:
    if not _HAS_WINRM:
        return {}
    user   = creds.get('user', '')
    passwd = creds.get('password', '')
    domain = creds.get('domain', '')
    login  = f'{domain}\\{user}' if domain else user
    try:
        sess = _winrm.Session(
            f'http://{ip}:5985/wsman',
            auth=(login, passwd),
            transport='ntlm',
            read_timeout_sec=timeout,
            operation_timeout_sec=timeout,
        )

        def ps(script: str) -> str:
            return sess.run_ps(script).std_out.decode(errors='replace').strip()

        data: dict = {'method': 'WinRM', 'platform': 'Windows'}
        data['os']  = ps('(Get-WmiObject Win32_OperatingSystem).Caption')[:80]
        cpu_name    = ps('(Get-WmiObject Win32_Processor | Select-Object -First 1).Name')
        cpu_cores   = ps('(Get-WmiObject Win32_Processor | Select-Object -First 1).NumberOfLogicalProcessors')
        data['cpu'] = f'{cpu_name[:40]} ({cpu_cores}c)' if cpu_name else ''
        ram_b = ps('(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory')
        data['ram']  = f'{int(ram_b) // (1024**3)} GB' if ram_b.isdigit() else ''
        data['disk'] = ps(
            'Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | '
            'Select-Object -First 1 | '
            'ForEach-Object { "{0:.0f} GB total, {1:.0f} GB free" -f ($_.Size/1GB),($_.FreeSpace/1GB) }'
        )[:40]
        data['uptime'] = ps(
            '(Get-WmiObject Win32_OperatingSystem).ConvertToDateTime('
            '(Get-WmiObject Win32_OperatingSystem).LastBootUpTime) | '
            'ForEach-Object { "up since " + $_.ToString("yyyy-MM-dd HH:mm") }'
        )[:60]
        return {k: v for k, v in data.items() if v}
    except Exception:
        return {}


def _collect_winrm(ip: str, creds_list: list[dict], timeout: int) -> dict:
    """Try each credential set in order; return data from the first that connects."""
    for creds in creds_list:
        if not creds.get('user'):
            continue
        result = _try_winrm(ip, creds, timeout)
        if result:
            return result
    return {'method': 'WinRM', 'error': 'pywinrm not installed'} if not _HAS_WINRM else {}


# ── SNMP collection ───────────────────────────────────────────────────────────

_SNMP_OIDS = {
    'os':     '1.3.6.1.2.1.1.1.0',
    'uptime': '1.3.6.1.2.1.1.3.0',
}


def _snmpget_val(ip: str, oid: str, version_args: list[str], timeout: int) -> str:
    if not _CMD_SNMPGET:
        return ''
    try:
        r = subprocess.run(
            [_CMD_SNMPGET, '-v', *version_args, '-t', str(timeout), '-r', '1', ip, oid],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        line = r.stdout.strip()
        return line.split('=', 1)[-1].split(':', 1)[-1].strip().strip('"') if '=' in line else ''
    except Exception:
        return ''


def _collect_snmp(ip: str, creds: dict, timeout: int) -> dict:
    version = creds.get('version', '2c')
    data: dict = {'method': 'SNMP', 'platform': 'Network'}

    if version in ('1', '2c'):
        v_args = [version, '-c', creds.get('community', 'public')]
    else:
        v_args = [
            '3', '-u', creds.get('user', ''),
            '-l', 'authPriv',
            '-a', creds.get('auth_proto', 'SHA'),
            '-A', creds.get('auth_pass', ''),
            '-x', creds.get('priv_proto', 'AES'),
            '-X', creds.get('priv_pass', ''),
        ]

    data['os']     = _snmpget_val(ip, _SNMP_OIDS['os'],     v_args, timeout)[:80]
    data['uptime'] = _snmpget_val(ip, _SNMP_OIDS['uptime'], v_args, timeout)[:60]
    return {k: v for k, v in data.items() if v}


# ── Port probe + ping ─────────────────────────────────────────────────────────

def _port_open(ip: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def _ping(ip: str, timeout: int = 1) -> bool:
    try:
        r = subprocess.run(
            ['ping', '-c', '1', '-W', str(timeout), ip],
            capture_output=True, timeout=timeout + 2,
        )
        return r.returncode == 0
    except Exception:
        return False


# Common ports for hosts that block ICMP (Windows Firewall default)
_ALIVE_PORTS = (22, 80, 443, 135, 445, 3389, 5985)

def _is_alive(ip: str, timeout: int = 1) -> bool:
    if _ping(ip, timeout=timeout):
        return True
    return any(_port_open(ip, p, timeout=1.0) for p in _ALIVE_PORTS)


# ── Per-host orchestration ────────────────────────────────────────────────────

def collect_host(
    ip: str,
    ssh_creds: list[dict],
    winrm_creds: list[dict],
    snmp_creds: dict,
    timeout: int = 5,
) -> dict | None:
    if not _is_alive(ip, timeout=1):
        return None

    base = _nmap_detect(ip, timeout=timeout)

    if ssh_creds and _port_open(ip, 22, timeout=1.5):
        result = _collect_ssh(ip, ssh_creds, timeout)
        if result:
            base.update(result)

    # Try WinRM independently — SSH may be open but irrelevant (e.g. Windows with OpenSSH)
    if not base.get('os') and winrm_creds and (_port_open(ip, 5985, 1.5) or _port_open(ip, 5986, 1.5)):
        result = _collect_winrm(ip, winrm_creds, timeout)
        if result:
            base.update(result)

    if not base.get('os') and snmp_creds and _port_open(ip, 161, 1.5):
        base.update(_collect_snmp(ip, snmp_creds, timeout))

    return base


# ── QThread worker ────────────────────────────────────────────────────────────

class AssetScanWorker(QThread):
    host_found = Signal(dict)
    progress   = Signal(int, int)
    finished_  = Signal()

    def __init__(
        self,
        cidr: str,
        ssh_creds: list[dict],
        winrm_creds: list[dict],
        snmp_creds: dict,
        timeout: int = 5,
        threads: int = 40,
    ) -> None:
        super().__init__()
        self._cidr        = cidr
        self._ssh_creds   = [dict(c) for c in ssh_creds]
        self._winrm_creds = [dict(c) for c in winrm_creds]
        self._snmp_creds  = dict(snmp_creds)
        self._timeout     = timeout
        self._threads     = threads
        self._stop        = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            hosts = [str(h) for h in ipaddress.ip_network(self._cidr, strict=False).hosts()]
        except ValueError:
            hosts = [self._cidr]

        total = len(hosts)
        done  = 0

        ssh_c   = [dict(c) for c in self._ssh_creds]
        winrm_c = [dict(c) for c in self._winrm_creds]
        snmp_c  = dict(self._snmp_creds)

        with ThreadPoolExecutor(max_workers=self._threads) as pool:
            futures = {
                pool.submit(collect_host, ip, ssh_c, winrm_c, snmp_c, self._timeout): ip
                for ip in hosts
            }
            for fut in as_completed(futures):
                if self._stop:
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                done += 1
                self.progress.emit(done, total)
                try:
                    asset = fut.result()
                    if asset:
                        self.host_found.emit(asset)
                except Exception:
                    pass

        for c in ssh_c:
            c.clear()
        for c in winrm_c:
            c.clear()
        snmp_c.clear()

        self.finished_.emit()
