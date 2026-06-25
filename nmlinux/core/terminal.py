"""PTY-backed SSH worker — runs in a QThread, emits raw PTY bytes."""

from __future__ import annotations

import os
import sys
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

    def run(self) -> None:
        code = -1
        try:
            _env = dict(os.environ)
            _env.setdefault('TERM', 'xterm-256color')
            # echo=True keeps the local PTY in normal mode so ssh propagates
            # ECHO-on to the remote pty (SSH pty-req carries the local tty modes).
            # ssh then switches the local side to raw for the session, so there is
            # no double echo. Forcing echo off here used to tell the remote
            # "no echo", which killed remote echo entirely — keystrokes were sent
            # to the shell but never displayed after login. See DT-14.
            self._proc = ptyprocess.PtyProcess.spawn(
                self._args, echo=True, dimensions=(self._rows, self._cols), env=_env
            )

            while self._proc.isalive():
                try:
                    raw = self._proc.read(4096)
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
