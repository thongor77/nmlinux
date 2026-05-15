"""PTY-backed SSH worker — runs in a QThread, emits output as plain text."""

from __future__ import annotations

import os
import re
import sys
import termios
import ptyprocess
from PySide6.QtCore import QThread, Signal

_DEBUG = os.environ.get('NMLINUX_DEBUG') == '1'


_ANSI_RE = re.compile(
    r'\x1b(?:'
    r'\[[0-9;?]*[ -/]*[@-~]'         # CSI  (cursor moves, colors, …)
    r'|\][^\x07\x1b]*[\x07\x1b]'     # OSC  (set title, …)
    r'|[@-Z\\-_]'                     # Fe   (SS2, SS3, …)
    r')'
)
# CSI CUB (cursor backward): \x1b[nD → convert to \x08 backspaces.
_CSI_CUB_RE = re.compile(r'\x1b\[(\d*)D')
# CSI CUF (cursor forward): \x1b[nC — ZSH Up-arrow skips over the prompt with this.
_CSI_CUF_RE = re.compile(r'\x1b\[(\d*)C')
# CSI EL (erase to end of line): \x1b[K or \x1b[0K — ZSH clears the input area.
_CSI_EL_RE  = re.compile(r'\x1b\[0?K')

# Private-Unicode sentinels: survive strip_ansi and are handled by _on_term_output.
ERASE_EOL    = ''   # erase from cursor to end of current line
CURSOR_RIGHT = ''   # move cursor right 1 column (one unit of CUF)

# Control chars stripped — keeps \x08 (backspace), \x09 (tab), \x0a (newline),
# \x0d (\r, carriage return).  \r is kept and handled by _on_term_output as
# "go to start of current line" so ZSH CR-based redraws overwrite in place.
_CTRL_RE = re.compile(r'[\x00-\x07\x0b-\x0c\x0e-\x1f\x7f]')


def strip_ansi(text: str) -> str:
    # Convert cursor-movement sequences to sentinels BEFORE generic stripping.
    text = _CSI_CUB_RE.sub(lambda m: '\x08' * (int(m.group(1)) if m.group(1) else 1), text)
    text = _CSI_CUF_RE.sub(lambda m: CURSOR_RIGHT * (int(m.group(1)) if m.group(1) else 1), text)
    text = _CSI_EL_RE.sub(ERASE_EOL, text)
    return _CTRL_RE.sub('', _ANSI_RE.sub('', text))


_CLEAR_SCREEN_RE = re.compile(r'\x1b\[2J')   # erase entire display (clear command)


class SshWorker(QThread):
    output       = Signal(str)   # stripped text ready to append
    exited       = Signal(int)   # exit code
    clear_screen = Signal()      # terminal sent an erase-display sequence

    def __init__(self, args: list[str], rows: int = 24, cols: int = 80) -> None:
        super().__init__()
        self._args  = args
        self._rows  = rows
        self._cols  = cols
        self._proc: ptyprocess.PtyProcess | None = None

    def _kill_echo(self) -> None:
        """Disable local PTY echo via termios (more reliable than ptyprocess.setecho)."""
        try:
            fd = self._proc.fd
            attrs = termios.tcgetattr(fd)
            if attrs[3] & termios.ECHO:
                attrs[3] &= ~(termios.ECHO | termios.ECHOE | termios.ECHOK | termios.ECHONL)
                termios.tcsetattr(fd, termios.TCSANOW, attrs)
        except Exception:
            pass

    def run(self) -> None:
        code = -1
        try:
            _env = dict(os.environ)
            _env.setdefault('TERM', 'xterm-256color')
            self._proc = ptyprocess.PtyProcess.spawn(
                self._args, echo=False, dimensions=(self._rows, self._cols), env=_env
            )
            self._kill_echo()

            # SSH resets termios during its handshake and may re-enable ECHO.
            # Enforce echo=off on the first several reads (covers the handshake window).
            _echo_checks = 0
            while self._proc.isalive():
                try:
                    raw = self._proc.read(4096)
                    if _echo_checks < 8:
                        _echo_checks += 1
                        self._kill_echo()
                    if _DEBUG:
                        print(f'READ  {raw!r}', file=sys.stderr, flush=True)
                    raw_str = raw.decode('utf-8', errors='replace')
                    if _CLEAR_SCREEN_RE.search(raw_str):
                        self.clear_screen.emit()
                    text = strip_ansi(raw_str)
                    if text:
                        self.output.emit(text)
                except EOFError:
                    break
            code = self._proc.exitstatus or 0
        except Exception as exc:
            self.output.emit(f"\n[Erreur démarrage SSH : {exc}]\n")
        finally:
            self.exited.emit(code)

    def write(self, text: str) -> None:
        if self._proc and self._proc.isalive():
            if _DEBUG:
                print(f'WRITE {text!r}', file=sys.stderr, flush=True)
            self._proc.write(text.encode('utf-8'))

    def resize(self, rows: int, cols: int) -> None:
        if self._proc and self._proc.isalive():
            try:
                self._proc.setwinsize(rows, cols)
            except Exception:
                pass

    def stop(self) -> None:
        if self._proc and self._proc.isalive():
            try:
                self._proc.terminate(force=True)
            except Exception:
                pass
        self.wait(2000)
