import sys
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from nmlinux.window import MainWindow
from nmlinux.core.icons import themed_icon


def _ensure_icon_theme() -> None:
    """When Qt has no icon theme set, detect it from the desktop environment."""
    if QIcon.themeName():
        return

    # KDE / KConfig (~/.config/kdeglobals)
    try:
        import configparser, os
        kdeglobals = os.path.expanduser("~/.config/kdeglobals")
        cfg = configparser.ConfigParser()
        cfg.read(kdeglobals)
        theme = cfg.get("Icons", "Theme", fallback="").strip()
        if theme:
            QIcon.setThemeName(theme)
            return
    except Exception:
        pass

    # GNOME / gsettings
    try:
        theme = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "icon-theme"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip().strip("'\"")
        if theme:
            QIcon.setThemeName(theme)
            return
    except Exception:
        pass

    # Fallback
    QIcon.setThemeName("breeze")


def main() -> None:
    app = QApplication(sys.argv)
    _ensure_icon_theme()
    app.setApplicationName("nmlinux")
    app.setApplicationDisplayName("NMLinux")
    app.setOrganizationName("nmlinux")
    app.setDesktopFileName("nmlinux")
    app.setWindowIcon(themed_icon("network-wired", "network-server", "applications-internet"))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
