from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

from game_version import LOBBY_VERSION

import options


class lobby(QtWidgets.QWidget):
    def __init__(self, _ao_app):
        super().__init__()
        self.ao_app = _ao_app

        #load the theme lobby.ui file
        theme = "default"
        ui_file = QFile(f"data/themes/{theme}/lobby.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        loaded = loader.load(ui_file, self)
        ui_file.close()
        if loaded is None:
            raise RuntimeError(f"Failed to load UI file: {ui_file.errorString()}")
        
        loaded.setParent(self)
        self.ui = loaded

        for w in self.ui.findChildren(QtWidgets.QWidget):
            name = w.objectName()
            if name:
                setattr(self, name, w)

        if hasattr(self.ui, "versiontext"):
            self.ui.versiontext.setText(f"Re: Attorney Investigations Online\nv{LOBBY_VERSION}")

        if hasattr(self.ui, "settingsbutton"):
            self.ui.settingsbutton.clicked.connect(self.on_settings_button)

        self.options_window = options.Options(_ao_app)

    def on_settings_button(self):
        self.options_window.show()
