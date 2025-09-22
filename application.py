from PySide6.QtWidgets import QApplication
from PySide6 import QtCore
from main_window import MainWindow

class Application(QApplication):
    player_id = -1
    charlist, musiclist, zonelist = [], [], []

    def __init__(self, argv=[]):
        super().__init__(argv)
        self.main_window = MainWindow(self)
        self.main_window.show()
        self.controls = {
            "up": [QtCore.Qt.Key_W, QtCore.Qt.Key_Up],
            "down": [QtCore.Qt.Key_S, QtCore.Qt.Key_Down],
            "left": [QtCore.Qt.Key_A, QtCore.Qt.Key_Left],
            "right": [QtCore.Qt.Key_D, QtCore.Qt.Key_Right],
            "run": [QtCore.Qt.Key_Shift, -1],
        }

class ClientThread:
    pass

class UDPThread:
    pass
