from PySide6.QtWidgets import QApplication
from main_window import MainWindow

class Application(QApplication):
    def __init__(self, argv=[]):
        super().__init__(argv)
        self.main_window = MainWindow(self)
        self.main_window.show()
    pass


class ClientThread:
    pass


class UDPThread:
    pass
