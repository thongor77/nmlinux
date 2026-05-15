"""Real terminal widget backed by pyte (VT100/VT220/xterm emulator).

Renders pyte.Screen directly with QPainter — no manual ANSI parsing needed.
"""

from __future__ import annotations

import pyte
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeyEvent, QPainter
from PySide6.QtWidgets import QApplication, QWidget

# ── Colour palette ──────────────────────────────────────────────────────────

# Catppuccin Mocha — same palette used in the old QPlainTextEdit terminal
_NAMED: dict[str, str] = {
    'black':         '#1e1e2e',
    'red':           '#f38ba8',
    'green':         '#a6e3a1',
    'brown':         '#f9e2af',   # dark yellow
    'blue':          '#89b4fa',
    'magenta':       '#cba6f7',
    'cyan':          '#89dceb',
    'white':         '#cdd6f4',
    'brightblack':   '#585b70',
    'brightred':     '#f38ba8',
    'brightgreen':   '#a6e3a1',
    'brightyellow':  '#f9e2af',
    'brightblue':    '#89b4fa',
    'brightmagenta': '#cba6f7',
    'brightcyan':    '#89dceb',
    'brightwhite':   '#cdd6f4',
}

_DEFAULT_FG = QColor('#cdd6f4')
_DEFAULT_BG = QColor('#1e1e2e')

# Build full 256-colour palette once at import time
_P256: dict[int, QColor] = {}

def _build_palette() -> None:
    named_hex = list(_NAMED.values())           # 0-15
    for i, h in enumerate(named_hex):
        _P256[i] = QColor(h)
    for i in range(216):                         # 16-231  (6×6×6 cube)
        r = (i // 36) * 51
        g = ((i // 6) % 6) * 51
        b = (i % 6) * 51
        _P256[16 + i] = QColor(r, g, b)
    for i in range(24):                          # 232-255 (grayscale)
        v = 8 + i * 10
        _P256[232 + i] = QColor(v, v, v)

_build_palette()


def _qcolor(spec: 'str | int | None', default: QColor) -> QColor:
    """Resolve a pyte colour spec to a QColor."""
    if spec is None or spec == 'default':
        return default
    if isinstance(spec, int):
        return _P256.get(spec, default)
    if isinstance(spec, str):
        if spec in _NAMED:
            return QColor(_NAMED[spec])
        if len(spec) == 6:          # pyte true-colour: 'rrggbb' hex string
            return QColor('#' + spec)
    return default


# ── Key maps ────────────────────────────────────────────────────────────────

_KEY_MAP: dict[Qt.Key, bytes] = {
    Qt.Key.Key_Up:       b'\x1b[A',
    Qt.Key.Key_Down:     b'\x1b[B',
    Qt.Key.Key_Right:    b'\x1b[C',
    Qt.Key.Key_Left:     b'\x1b[D',
    Qt.Key.Key_Home:     b'\x1b[H',
    Qt.Key.Key_End:      b'\x1b[F',
    Qt.Key.Key_Delete:   b'\x1b[3~',
    Qt.Key.Key_PageUp:   b'\x1b[5~',
    Qt.Key.Key_PageDown: b'\x1b[6~',
    Qt.Key.Key_Insert:   b'\x1b[2~',
    Qt.Key.Key_F1:       b'\x1bOP',
    Qt.Key.Key_F2:       b'\x1bOQ',
    Qt.Key.Key_F3:       b'\x1bOR',
    Qt.Key.Key_F4:       b'\x1bOS',
    Qt.Key.Key_F5:       b'\x1b[15~',
    Qt.Key.Key_Backtab:  b'\x1b[Z',
}
_CTRL_MAP: dict[Qt.Key, bytes] = {
    Qt.Key.Key_C: b'\x03', Qt.Key.Key_D: b'\x04', Qt.Key.Key_Z: b'\x1a',
    Qt.Key.Key_L: b'\x0c', Qt.Key.Key_A: b'\x01', Qt.Key.Key_E: b'\x05',
    Qt.Key.Key_U: b'\x15', Qt.Key.Key_K: b'\x0b', Qt.Key.Key_W: b'\x17',
    Qt.Key.Key_R: b'\x12',
}
_MODIFIER_KEYS = frozenset([
    Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
    Qt.Key.Key_AltGr, Qt.Key.Key_CapsLock, Qt.Key.Key_NumLock,
    Qt.Key.Key_ScrollLock, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R,
])


# ── Widget ──────────────────────────────────────────────────────────────────

class TerminalView(QWidget):
    """QPainter-rendered terminal backed by a pyte.Screen.

    Usage:
        view = TerminalView()
        view.set_writer(worker.write)           # bytes → PTY
        view.resize_pty.connect(worker.resize)  # rows, cols → SIGWINCH
        worker.output.connect(view.feed)        # raw bytes → pyte
    """

    resize_pty = Signal(int, int)   # (rows, cols)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        mono = QFont('Monospace')
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        mono.setPointSize(10)
        self._font      = mono
        self._font_bold = QFont(mono)
        self._font_bold.setBold(True)
        fm              = QFontMetrics(mono)
        self._cw        = fm.horizontalAdvance('M')
        self._ch        = fm.height()
        self._ascent    = fm.ascent()

        self._screen = pyte.Screen(80, 24)
        self._stream = pyte.ByteStream(self._screen)

        self._cursor_on = True
        _blink = QTimer(self)
        _blink.setInterval(530)
        _blink.timeout.connect(self._toggle_cursor)
        _blink.start()

        self._writer: 'Callable[[bytes], None] | None' = None

    # ── Public API ──────────────────────────────────────────────────────────

    def set_writer(self, fn: 'Callable[[bytes], None]') -> None:
        """Register callback that forwards keyboard input to the PTY."""
        self._writer = fn

    def feed(self, data: bytes) -> None:
        """Feed raw PTY output into pyte and schedule a repaint."""
        self._stream.feed(data)
        self.update()

    def reset_screen(self) -> None:
        """Hard-reset the pyte screen (new session)."""
        self._screen.reset()
        self.update()

    # ── Rendering ───────────────────────────────────────────────────────────

    def _toggle_cursor(self) -> None:
        self._cursor_on = not self._cursor_on
        cx = self._screen.cursor.x * self._cw
        cy = self._screen.cursor.y * self._ch
        self.update(cx, cy, self._cw + 1, self._ch + 1)

    def paintEvent(self, _event) -> None:                   # noqa: N802
        p = QPainter(self)
        p.fillRect(self.rect(), _DEFAULT_BG)
        p.setFont(self._font)

        buf = self._screen.buffer
        for y in range(self._screen.lines):
            row = buf.get(y, {})
            for x in range(self._screen.columns):
                cell = row.get(x)
                if cell is None:
                    continue

                char = cell.data or ' '
                rev  = getattr(cell, 'reverse', False)

                fg_spec = cell.bg if rev else cell.fg
                bg_spec = cell.fg if rev else cell.bg

                fg = _qcolor(fg_spec, _DEFAULT_FG)
                bg = _qcolor(bg_spec, _DEFAULT_BG)

                rx = x * self._cw
                ry = y * self._ch

                if bg != _DEFAULT_BG:
                    p.fillRect(rx, ry, self._cw, self._ch, bg)

                if char != ' ':
                    p.setFont(self._font_bold if getattr(cell, 'bold', False)
                              else self._font)
                    p.setPen(fg)
                    p.drawText(rx, ry + self._ascent, char)

        # Block cursor
        if self._cursor_on and self.hasFocus():
            cx = self._screen.cursor.x * self._cw
            cy = self._screen.cursor.y * self._ch
            p.fillRect(cx, cy, self._cw, self._ch, QColor(200, 200, 200, 170))

    # ── Resize ──────────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:                   # noqa: N802
        super().resizeEvent(event)
        cols = max(10, self.width()  // self._cw)
        rows = max(3,  self.height() // self._ch)
        if cols != self._screen.columns or rows != self._screen.lines:
            self._screen.resize(rows, cols)
            self.resize_pty.emit(rows, cols)

    # ── Keyboard ────────────────────────────────────────────────────────────

    def focusNextPrevChild(self, _next: bool) -> bool:
        return False   # prevent Tab from moving focus

    def keyPressEvent(self, event: QKeyEvent) -> None:      # noqa: N802
        if self._writer is None:
            return

        key  = event.key()
        mods = event.modifiers()

        if key in _MODIFIER_KEYS:
            return

        # Ctrl+Shift+C/V — copy / paste
        cs = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        if mods == cs:
            if key == Qt.Key.Key_V:
                txt = QApplication.clipboard().text()
                if txt:
                    self._writer(txt.encode('utf-8'))
            return

        # Ctrl sequences
        if mods == Qt.KeyboardModifier.ControlModifier:
            seq = _CTRL_MAP.get(key)
            if seq:
                self._writer(seq)
                return

        # Tab (must come before KEY_MAP check so it isn't swallowed)
        if key == Qt.Key.Key_Tab:
            self._writer(b'\t')
            return

        # Special keys (arrows, F-keys, …)
        seq = _KEY_MAP.get(key)
        if seq:
            self._writer(seq)
            return

        # Printable text
        txt = event.text()
        if txt:
            self._writer(b'\x7f' if txt == '\x08' else txt.encode('utf-8'))
