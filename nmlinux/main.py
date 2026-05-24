import sys
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from nmlinux.window import MainWindow
from nmlinux.core.icons import themed_icon


def _icon_ok(name: str) -> bool:
    """True if the theme provides a real pixmap for *name* at any standard size."""
    icon = QIcon.fromTheme(name)
    if icon.isNull():
        return False
    for size in (22, 24, 16, 32, 48):
        if not icon.pixmap(size, size).isNull():
            return True
    return False


def _ensure_icon_theme() -> None:
    """When Qt has no icon theme set, detect it from the desktop environment."""
    import os

    # Add non-standard icon search paths (NixOS, Nix profiles, custom installs)
    # Qt expects the *parent* of the icons/ directory, i.e. /foo/share not /foo/share/icons
    extra_search = [
        "/run/current-system/sw/share",
        os.path.expanduser("~/.nix-profile/share"),
        "/usr/local/share",
    ]
    current_paths = QIcon.themeSearchPaths()
    additions = [p for p in extra_search if os.path.isdir(p) and p not in current_paths]
    if additions:
        QIcon.setThemeSearchPaths(additions + current_paths)

    # Explicit Nix wrapper override (NMLINUX_ICON_PATH = <store>/share, has icons/breeze/)
    icon_path = os.environ.get("NMLINUX_ICON_PATH", "").strip()
    if icon_path:
        if icon_path not in QIcon.themeSearchPaths():
            QIcon.setThemeSearchPaths([icon_path] + QIcon.themeSearchPaths())
        # Nix bundle ships Breeze — force the theme name so Qt uses it
        if os.path.isdir(os.path.join(icon_path, "icons", "breeze")):
            QIcon.setThemeName("breeze")
            if _icon_ok("network-wired"):
                return

    # If the current theme already resolves real icons, nothing to do
    if QIcon.themeName() and _icon_ok("network-wired"):
        return

    # KDE / KConfig (~/.config/kdeglobals, /etc/xdg/kdeglobals for NixOS)
    try:
        import configparser
        for kdeglobals in (
            os.path.expanduser("~/.config/kdeglobals"),
            "/etc/xdg/kdeglobals",
        ):
            cfg = configparser.ConfigParser()
            cfg.read(kdeglobals)
            theme = cfg.get("Icons", "Theme", fallback="").strip()
            if theme:
                QIcon.setThemeName(theme)
                if _icon_ok("network-wired"):
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
            if _icon_ok("network-wired"):
                return
    except Exception:
        pass

    # Fallback: try breeze then Adwaita
    for name in ("breeze", "Adwaita", "hicolor"):
        QIcon.setThemeName(name)
        if _icon_ok("network-wired"):
            return


def _debug_icons() -> None:
    import os
    from PySide6.QtWidgets import QApplication as _QApp
    from PySide6.QtCore import QCoreApplication
    app = _QApp(sys.argv)
    _ensure_icon_theme()
    print("=== nmlinux icon debug ===")
    print(f"QT_QPA_PLATFORMTHEME : {os.environ.get('QT_QPA_PLATFORMTHEME', 'NOT SET')}")
    print(f"QT_PLUGIN_PATH       : {os.environ.get('QT_PLUGIN_PATH', 'NOT SET')}")
    print(f"NMLINUX_ICON_PATH    : {os.environ.get('NMLINUX_ICON_PATH', 'NOT SET')}")
    print(f"themeName            : {QIcon.themeName()!r}")
    print(f"libraryPaths         : {QCoreApplication.libraryPaths()}")
    # Check if icon files actually exist on disk
    icon_path = os.environ.get("NMLINUX_ICON_PATH", "")
    for rel in (
        "icons/breeze/index.theme",
        "icons/breeze/scalable/devices/network-wired.svg",
        "icons/breeze/scalable/devices/network-wired.svgz",
        "icons/breeze/22/devices/network-wired.png",
    ):
        full = os.path.join(icon_path, rel)
        print(f"  exists {full}: {os.path.exists(full)}")
    for iname in ("network-wired", "network-wireless"):
        icon = QIcon.fromTheme(iname)
        sizes = {s: not icon.pixmap(s, s).isNull() for s in (16, 22, 24, 32, 48)}
        print(f"  {iname}: isNull={icon.isNull()}  pixmaps={sizes}")
    sys.exit(0)


def main() -> None:
    if "--debug-icons" in sys.argv:
        _debug_icons()
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
