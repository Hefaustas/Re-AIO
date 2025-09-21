from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QStackedWidget

import lobby

class MainWindow(QMainWindow):
    def __init__(self, _ao_app):
        super().__init__()
        self.ao_app = _ao_app

        self.stackwidget = QStackedWidget(self)
        self.lobbywidget = lobby.lobby(self.ao_app)
        
        self.setCentralWidget(self.stackwidget)
        self.stackwidget.addWidget(self.lobbywidget)
        self.setWindowTitle("Re: Attorney Investigations Online")
        self.setWindowFlags(self.windowFlags() & ~0x00040000)  # grey out maximize button
        
        try:
            ui_size = self.lobbywidget.ui.size()
        except Exception:
            ui_size = self.lobbywidget.sizeHint()
        if ui_size.isValid():
            self.setFixedSize(ui_size)
        else:
            self.resize(600, 800)

    def startGame(self):
        pass

    def stopGame(self):
        pass

    def showServers(self):
        pass

    def center(self):
        pass