from PySide6.QtWidgets import QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

class lobby(QWidget):
    def __init__(self, _ao_app):
        super().__init__()
        self.ao_app = _ao_app

        #load the theme lobby.ui file
        theme = "default"
        ui_file = QFile(f"data/themes/{theme}/lobby.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()