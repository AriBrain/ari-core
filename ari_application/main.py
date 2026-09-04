# === Standard Library Imports ===
import sys
import os
import time
import traceback

# === Third-Party Library Imports ===
import qdarktheme
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

# === Internal Application Imports ===
from ari_application import get_package_dir
from ari_application.ui.main_window import BrainNav
from ari_application.ui.start_window import StartWindow
from ari_application.ui.splash_screen import SplashScreen
from ari_application.ui.components.message_box import MessageLogger


def _install_excepthook():
    """
    Route uncaught exceptions to the in-app MessageLogger when one exists.
    Always also defer to the default hook so the traceback still reaches stderr
    and any debugger attached to the process.
    """
    default_hook = sys.excepthook

    def hook(exc_type, exc_value, exc_tb):
        default_hook(exc_type, exc_value, exc_tb)
        active = MessageLogger.get_active()
        if active is None:
            return
        try:
            active.error(
                f"Uncaught {exc_type.__name__}: {exc_value}",
                exc_info=(exc_type, exc_value, exc_tb),
            )
        except Exception:
            # If the UI itself is in a broken state, swallow — the default hook
            # has already printed to stderr.
            traceback.print_exc()

    sys.excepthook = hook


def main():
    # Enable HiDPI for better scaling on high-resolution displays
    # qdarktheme.enable_hi_dpi()

    _install_excepthook()

    app = QApplication(sys.argv)
    # Apply the Fusion theme
    # app.setStyle("Fusion")

    # Apply dark theme
    qdarktheme.setup_theme("dark")

    # Set the window icon
    icon_path = os.path.join(get_package_dir(), 'public', 'logo.jpg')
    app.setWindowIcon(QIcon(icon_path))

    # Create and display the splash screen
    splash = SplashScreen()
    splash.show()

    # Simulate a loading process
    for i in range(1, 3):
        splash.show_message(f"Loading...")  # Simulating some loading time
        time.sleep(0.10)

    # Start with the StartWindow
    start_window = StartWindow()
    start_window.show()

    splash.finish(start_window) 

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()