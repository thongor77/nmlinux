"""PTY-backed SSH worker — runs in a QThread, emits raw PTY bytes."""

from __future__ import annotations

import os
import sys
import termios
import ptyprocess
from PySide6.QtCore import QThread, Signal


_DEBUG = os.environ.get('NMLINUX_DEBUG') == '1'


class SshWorker(QThread):
    output = Signal(bytes)   # raw PTY output → feed directly to pyte
    exited = Signal(int)     # exit code

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
            _echo_checks = 0
            while self._proc.isalive():
                try:
                    raw = self._proc.read(4096)
                    if _echo_checks < 8:
                        _echo_checks += 1
                        self._kill_echo()
                    if _DEBUG:
                        print(f'READ  {raw!r}', file=sys.stderr, flush=True)
                    self.output.emit(raw)
                except EOFError:
                    break
            code = self._proc.exitstatus or 0
        except Exception as exc:
            self.output.emit(f"\n[Erreur démarrage SSH : {exc}]\n".encode('utf-8'))
        finally:
            self.exited.emit(code)

    def write(self, data: bytes) -> None:
        if self._proc and self._proc.isalive():
            if _DEBUG:
                print(f'WRITE {data!r}', file=sys.stderr, flush=True)
            self._proc.write(data)

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
