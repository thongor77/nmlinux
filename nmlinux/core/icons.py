from PySide6.QtGui import QIcon


def themed_icon(*names: str) -> QIcon:
    """Return the first available theme icon from the given name list."""
    for name in names:
        icon = QIcon.fromTheme(name)
        if icon.isNull():
            continue
        # Try standard sizes: 22 (KDE/Breeze), 24 (GNOME/Adwaita), 16, 32, 48
        for size in (22, 24, 16, 32, 48):
            if not icon.pixmap(size, size).isNull():
                return icon
    return QIcon()
