import sys
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from nmlinux.window import MainWindow
from nmlinux.core.icons import themed_icon


def _ensure_icon_theme() -> None:
    """On GNOME/non-KDE desktops Qt often has no icon theme — detect and set one."""
    if QIcon.themeName():
        return
    # Try to read the GTK/GNOME icon theme from gsettings
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
    QIcon.setThemeName("Adwaita")


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
