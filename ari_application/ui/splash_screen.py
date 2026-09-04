import os

from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from ari_application import get_package_dir

class SplashScreen(QSplashScreen):
    def __init__(self):
        logo_path = os.path.join(get_package_dir(), 'public', 'logo.jpg')
        
        # Load the logo image
        pixmap = QPixmap(logo_path)

        # Resize the logo image
        target_width = 400  # Set your desired width
        target_height = 400  # Set your desired height
        pixmap = pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMask(pixmap.mask())

    def show_message(self, message):
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, Qt.white)