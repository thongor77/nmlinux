import sys
from PySide6.QtWidgets import QApplication
from nmlinux.window import MainWindow
from nmlinux.core.icons import themed_icon


def main() -> None:
    app = QApplication(sys.argv)
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
