import sys
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from nmlinux.window import MainWindow
from nmlinux.core.icons import themed_icon


def _ensure_icon_theme() -> None:
    """When Qt has no icon theme set, detect it from the desktop environment."""
    import os

    # Add non-standard icon search paths (NixOS, Nix profiles, custom installs)
    extra_search = [
        "/run/current-system/sw/share/icons",
        os.path.expanduser("~/.nix-profile/share/icons"),
        "/usr/local/share/icons",
    ]
    current_paths = QIcon.themeSearchPaths()
    additions = [p for p in extra_search if os.path.isdir(p) and p not in current_paths]
    if additions:
        QIcon.setThemeSearchPaths(additions + current_paths)

    # Explicit Nix wrapper override (NMLINUX_ICON_PATH points to icons dir)
    icon_path = os.environ.get("NMLINUX_ICON_PATH", "").strip()
    if icon_path and icon_path not in QIcon.themeSearchPaths():
        QIcon.setThemeSearchPaths([icon_path] + QIcon.themeSearchPaths())

    # If the current theme already resolves real icons, nothing to do
    if QIcon.themeName() and not QIcon.fromTheme("network-wired").isNull():
        return

    # KDE / KConfig (~/.config/kdeglobals)
    try:
        import configparser
        kdeglobals = os.path.expanduser("~/.config/kdeglobals")
        cfg = configparser.ConfigParser()
        cfg.read(kdeglobals)
        theme = cfg.get("Icons", "Theme", fallback="").strip()
        if theme:
            QIcon.setThemeName(theme)
            if not QIcon.fromTheme("network-wired").isNull():
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
            if not QIcon.fromTheme("network-wired").isNull():
                return
    except Exception:
        pass

    # Fallback: try breeze then Adwaita
    for name in ("breeze", "Adwaita", "hicolor"):
        QIcon.setThemeName(name)
        if not QIcon.fromTheme("network-wired").isNull():
            return


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
