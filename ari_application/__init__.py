import os
import sys


def get_package_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'ari_application')
    return os.path.dirname(os.path.abspath(__file__))