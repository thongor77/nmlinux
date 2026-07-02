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


def main() -> None:
    # macOS: NSBundle.mainBundle() resolves to the Python.framework bundle whose
    # CFBundleName is "Python". Qt reads this dict during QApplication construction
    # and uses it as the application menu title. We must patch the dict AND set the
    # process name before QApplication is created.
    if sys.platform == 'darwin':
        import os
        _brew_paths = '/opt/homebrew/bin:/usr/local/bin'
        if _brew_paths not in os.environ.get('PATH', ''):
            os.environ['PATH'] = _brew_paths + ':' + os.environ.get('PATH', '')

        sys.argv[0] = 'NMLinux'
        import ctypes
        try:
            ctypes.CDLL(None).setprogname(b'NMLinux')
        except Exception:
            pass
        try:
            from Foundation import NSBundle, NSProcessInfo
            _info = NSBundle.mainBundle().infoDictionary()
            _info['CFBundleName'] = 'NMLinux'
            _info['CFBundleDisplayName'] = 'NMLinux'
            _info['NSLocationWhenInUseUsageDescription'] = (
                'NMLinux needs Location Services to display Wi-Fi network names.'
            )
            NSProcessInfo.processInfo().setProcessName_('NMLinux')
        except Exception:
            pass

        # Request Location Services for Wi-Fi SSID access (macOS 13+)
        try:
            from CoreLocation import CLLocationManager
            if CLLocationManager.authorizationStatus() == 0:  # notDetermined
                global _cl_manager  # keep reference to prevent GC before dialog shows
                _cl_manager = CLLocationManager.alloc().init()
                _cl_manager.requestWhenInUseAuthorization()
        except Exception:
            pass

    app = QApplication(sys.argv)
    _ensure_icon_theme()
    app.setApplicationName("NMLinux")
    app.setApplicationDisplayName("NMLinux")

    # Belt-and-suspenders: rename any remaining "Python" in the native app menu
    if sys.platform == 'darwin':
        try:
            import AppKit
            menu = AppKit.NSApp.mainMenu()
            if menu and menu.numberOfItems() > 0:
                item = menu.itemAtIndex_(0)
                item.setTitle_('NMLinux')
                if item.submenu():
                    for i in range(item.submenu().numberOfItems()):
                        sub = item.submenu().itemAtIndex_(i)
                        if sub and 'Python' in (sub.title() or ''):
                            sub.setTitle_(sub.title().replace('Python', 'NMLinux'))
        except Exception:
            pass
    app.setOrganizationName("nmlinux")
    app.setDesktopFileName("nmlinux")
    app.setWindowIcon(themed_icon("network-wired", "network-server", "applications-internet"))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
