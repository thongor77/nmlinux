from PySide6.QtGui import QIcon


def themed_icon(*names: str) -> QIcon:
    """Return the first available theme icon from the given name list."""
    for name in names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull() and not icon.pixmap(24, 24).isNull():
            return icon
    return QIcon()
