from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

from game_version import LOBBY_VERSION

import options


class lobby(QtWidgets.QWidget):
    def __init__(self, _ao_app):
        super().__init__()
        self.ao_app = _ao_app

        TEST_SERVER1 = {
            "name": "Re:AIO First Server",
            "player_count": 11,
            "player_max": 20,
            "ping": 74,
            "version": "v0.1",
            "description": "FS is the first server ever published on Re:AIO. Featuring an amazing cast of AAI characters for roleplays, cases and investigations alike! Lorem ipsum dolor sit amet."
        }

        TEST_SERVER2 = {
            "name": "Re:AIO Second Server",
            "player_count": 5,
            "player_max": 16,
            "ping": 54,
            "version": "v0.1",
            "description": "Lorem ipsum"
        }

        SERVERS = [TEST_SERVER1, TEST_SERVER2]

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

        self.fix_headers(self.ui)

        self.ui.publicServerList.itemSelectionChanged.connect(self.on_selection_changed)
        self.ui.favoritesServerList.itemSelectionChanged.connect(self.on_selection_changed)

        for w in self.ui.findChildren(QtWidgets.QWidget):
            name = w.objectName()
            if name:
                setattr(self, name, w)

        if hasattr(self.ui, "versionText"):
            self.ui.versionText.setText(f"Re: Attorney Investigations Online\nv{LOBBY_VERSION}")

        if hasattr(self.ui, "settingsButton"):
            self.ui.settingsButton.clicked.connect(self.on_settings_button)

        if hasattr(self.ui, "directConnectButton"):
            self.ui.directConnectButton.clicked.connect(self.on_direct_connect_button)

        self.options_window = options.Options(_ao_app)

        for i in SERVERS:
            self.add_server(self.ui.publicServerList, i)

    def on_settings_button(self):
        self.options_window.showSettings()
        self.options_window.show()

    def add_server(self, tree, server):
        item = QtWidgets.QTreeWidgetItem([
            server["name"],
            f'{server["player_count"]}/{server["player_max"]}',
            f'{server["ping"]} ms',
            server["version"]

        ])

        item.setToolTip(0, server.get("description", ""))
        tree.addTopLevelItem(item)
    
    def on_selection_changed():
        pass

    def on_double_click():
        pass

    def fix_headers(self, ui):
        #set name headers to be largest.
        header = ui.publicServerList.header()

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)

        ui.publicServerList.setColumnWidth(0, 250)
        ui.publicServerList.setColumnWidth(1, 100)
        ui.publicServerList.setColumnWidth(2, 50)
        ui.publicServerList.setColumnWidth(3, 50)


        header = ui.favoritesServerList.header()

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)

        ui.favoritesServerList.setColumnWidth(0, 250)
        ui.favoritesServerList.setColumnWidth(1, 100)
        ui.favoritesServerList.setColumnWidth(2, 50)
        ui.favoritesServerList.setColumnWidth(3, 50)

    def on_refresh_button():
        pass

    def on_direct_connect_button(self):
        address, ok = QtWidgets.QInputDialog.getText(self, "Direct Connect", "Enter the IP address or URL of the server you wish to join. \nIt must have the format \"ip:port\"\nExample: 127.0.0.1:27010")
        # add ability to add favorites from this dialog when favoriting exists.
        pass