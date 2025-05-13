# === Standard Library Imports ===
import sys
import os
import time

# === Third-Party Library Imports ===
import qdarktheme
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

# === Internal Application Imports ===
from ari_application.ui.main_window import BrainNav
from ari_application.ui.start_window import StartWindow
from ari_application.ui.splash_screen import SplashScreen

def main():   
    # Enable HiDPI for better scaling on high-resolution displays
    # qdarktheme.enable_hi_dpi()
    
    app = QApplication(sys.argv)
    # Apply the Fusion theme
    # app.setStyle("Fusion")

    # Apply dark theme
    qdarktheme.setup_theme("dark")

    # Set the window icon
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'public', 'logo.jpg'))
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