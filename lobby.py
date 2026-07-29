import socket
import struct
import zlib
import configparser
import re
import html

from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, Qt

import aio_protocol
from packing import *

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

        self.servers = []
        self.favorites = []
        self.pinged_list = []
        self.ao_app.udpthread.info_received.connect(self.got_udp_request)

        self.serverselected = -1
        self.current_tab = 0

        self.fix_headers(self.ui)

        # sorts by players on boot
        # TODO: make it sort by player count only not by sum of player count and max players
        self.ui.publicServerList.sortByColumn(1, Qt.SortOrder.AscendingOrder)

        self.ui.publicServerList.itemSelectionChanged.connect(self.on_selection_changed)
        self.ui.favoritesServerList.itemSelectionChanged.connect(self.on_selection_changed)

        config = configparser.ConfigParser()
        config.read("re-aio.ini")

        ms_value = config.get(
            "Advanced",
            "master_server",
            fallback=config.get("MasterServer", "IP", fallback="193.26.159.112:27011")
        )
        ms_type = config.getboolean("Advanced", "ms_type", fallback=True)
        #backwards compatibility is king
        legacy_mode = (ms_type == True)
        self.legacy_mode = legacy_mode

        parts = ms_value.split(":", 1)
        ip = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 27011

        self.msthread = MasterServerThread(ip, port, legacy_mode=legacy_mode)

        self.msthread.serversReceived.connect(self.got_server_list)
        self.msthread.newsReceived.connect(self.got_news)
        self.msthread.error.connect(self.MS_error)

        self.msthread.start()

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

        if hasattr(self.ui, "refreshButton"):
            self.ui.refreshButton.clicked.connect(self.on_refresh_button)

        if hasattr(self.ui, "serverTabs"):
            self.ui.serverTabs.currentChanged.connect(self.on_tab_changed)

        self._init_server_info_widgets(server=None)
        self._update_server_info(None)

        self.options_window = options.Options(_ao_app)

    def closeEvent(self, event):
        if hasattr(self, "msthread") and self.msthread.isRunning():
            self.msthread.stop()
        super().closeEvent(event)

    def _init_server_info_widgets(self, server):
        self.server_name_label = QtWidgets.QLabel("", self.ui.serverName)
        self.server_name_label.setGeometry(6, 2, self.ui.serverName.width() - 12, self.ui.serverName.height() - 4)
        self.server_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.server_playercount_label = QtWidgets.QLabel("Players: 0/0", self.ui.serverPlayercount)
        self.server_playercount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.server_playercount_label.setGeometry(6, 2, self.ui.serverPlayercount.width() - 12, self.ui.serverPlayercount.height() - 4)
        self.server_description_label = QtWidgets.QLabel("", self.ui.serverDescription)
        self.server_description_label.setGeometry(6, 6, self.ui.serverDescription.width() - 12, self.ui.serverDescription.height() - 12)
        self.server_description_label.setWordWrap(True)
        self.server_description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # for clickable URLs
        self.server_description_label.setTextFormat(Qt.TextFormat.RichText)
        self.server_description_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.server_description_label.setOpenExternalLinks(True)

    def _update_server_info(self, server):
        if not server:
            self.server_name_label.setText("")
            self.server_playercount_label.setText("Players: 0/0")
            self.server_description_label.setText("")
            return
        clean_name, player_count, player_max = self._format_server_info(
            server.get("name", ""),
            server.get("player_count", 0),
            server.get("player_max", 0)
        )
        self.server_name_label.setText(clean_name)
        self.server_playercount_label.setText(f"{player_count}/{player_max}")
        self.server_playercount_label.setToolTip("Players")

        self.formatted_desc = self._format_description_for_display(server.get("description", ""))
        self.server_description_label.setText(self.formatted_desc)
    
    def got_server_list(self, servers):
        self.servers = servers

        if self.current_tab == 0:
            self.pinged_list = []
            for s in servers:
                self.pinged_list.append({
                    "name": s.get("name", f'{s["ip"]}:{s["port"]}'),
                    "player_count": 0,
                    "player_max": 0,
                    "ping": "--",
                    "version": s.get("version", "Legacy" if self.legacy_mode else "?"),
                    "description": s.get("description", ""),
                    "ip": s["ip"],
                    "port": s["port"],
                })

            self.update_server_list(self.pinged_list)
            for s in servers:
                self.ao_app.udpthread.send_info_request((s["ip"], s["port"]))

    def got_udp_request(self, server):
        addr, name, description, players, max_players, version, ping = server
        ip, port = addr

        for item in self.pinged_list:
            if item.get("ip") == ip and int(item.get("port")) == int(port):
                item["name"] = name
                item["description"] = description
                item["player_count"] = players
                item["player_max"] = max_players
                item["version"] = str(version)
                item["ping"] = ping
                break

        self.update_server_list(self.pinged_list)

    def got_news(self, news):
        pass

    def MS_error(self, message):
        QtWidgets.QMessageBox.critical(
            self,
            "Error connecting to master server",
            "Failed to connect to the master server.\n\n"
            "Check your internet connection, firewall, or antivirus.\n\n"
            f"Additional information:\n{message}"
        )

    def update_server_list(self, servers=None):
        if servers is None:
            servers = self.pinged_list

        self.ui.publicServerList.clear()
        for server in servers:
            self.add_server(self.ui.publicServerList, server)


    def on_settings_button(self):
        self.options_window.showSettings()
        self.options_window.show()

    def add_server(self, tree, server):
        raw_name = server.get("name", f'{server.get("ip", "?")}:{server.get("port", "?")}')

        if self.legacy_mode:
            #legacy masterserver puts playercount in server name 
            display_name, player_count, player_max = self._format_server_info(
                raw_name, server.get("player_count", 0), server.get("player_max", 0)
            )
        else:
            display_name = str(raw_name).strip()
            try:
                player_count = int(server.get("player_count", 0))
            except (TypeError, ValueError):
                player_count = 0
            try:
                player_max = int(server.get("player_max", 0))
            except (TypeError, ValueError):
                player_max = 0

        ping = server.get("ping", "--")
        version = str(server.get("version", "Legacy" if self.legacy_mode else "?"))

        item = QtWidgets.QTreeWidgetItem([
            display_name,
            f"{player_count}/{player_max}",
            f"{ping} ms" if str(ping).isdigit() else str(ping),
            version
        ])

        item.setToolTip(0, server.get("description", ""))
        tree.addTopLevelItem(item)
        
    def on_selection_changed(self):
        tree = self.sender()
        if tree is self.ui.publicServerList:
            self.current_tab = 0
            source = self.pinged_list
        elif tree is self.ui.favoritesServerList:
            self.current_tab = 1
            source = self.favorites
        else:
            source = self.pinged_list if self.current_tab == 0 else self.favorites
            tree = self.ui.publicServerList if self.current_tab == 0 else self.ui.favoritesServerList

        item = tree.currentItem()
        if item is None:
            self.serverselected = -1
            self._update_server_info(None)
            return
        index = tree.indexOfTopLevelItem(item)
        self.serverselected = index

        if 0 <= index < len(source) and isinstance(source[index], dict):
            self._update_server_info(source[index])
        else:
            self._update_server_info(None)

    def on_double_click():
        pass

    def fix_headers(self, ui):
        #set name header to be largest.
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

    def on_refresh_button(self):
        self.pinged_list = []
        self.update_server_list([])
        self.msthread.request_server_list()

    def on_direct_connect_button(self):
        address, ok = QtWidgets.QInputDialog.getText(self, "Direct Connect", "Enter the IP address or URL of the server you wish to join. \nIt must have the format \"ip:port\"\nExample: 127.0.0.1:27010")
        # add ability to add favorites from this dialog when favoriting exists.
        pass

    def on_tab_changed(self, index):
        self.current_tab = index
        self.serverselected = -1
        self._update_server_info(None)

    # should turn "Server [13/37]"" into "Name: Server | Players: 13/37"
    # regex is witchcraft
    def _format_server_info(self, raw_name, player_count=0, player_max=0):
        name = str(raw_name or "").strip()
        match = re.match(r"^(.*?)(?:\s*\[(\d+)\s*/\s*(\d+)\])?\s*$", name)
        if match:
            clean_name = match.group(1).strip()
            count = match.group(2)
            max = match.group(3)
            if count is not None and max is not None:
                player_count = int(count)
                player_max = int(max)

        else:
            clean_name = name

        try:
            player_count = int(player_count)
        except (TypeError, ValueError):
            player_count = 0
        try:
            player_max = int(player_max)
        except (TypeError, ValueError):
            player_max = 0

        return clean_name, player_count, player_max

    def _format_description_for_display(self, raw_description):
        #ms sends <num> for line breaks
        text = str(raw_description or "").replace("<num>", "#")
        text = text.replace("##", "\n\n").replace("#", "\n")

        #turn urls into clcikable links.
        safe = html.escape(text)
        safe = re.sub(r'(https?://[^\s<]+)', r'<a href="\1">\1</a>', safe)

        return safe.replace("\n", "<br>")


# keepalives temporarily disabled
class MasterServerThread(QThread):

    serversReceived = Signal(list)
    newsReceived = Signal(str)
    error = Signal(str)

    def __init__(self, host, port, legacy_mode=True):
        super().__init__()
        self.host = host
        self.port = port
        self.legacy_mode = legacy_mode
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.legacy_buffer = ""
        #self.keepalive_timer = 2700

    def run(self):
        try:
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(0.1)

        except OSError as e:
            self.error.emit(str(e))
            return

        if self.legacy_mode:
            self.request_server_list()

        while self.running:
            '''
            self.keepalive_timer -=1
            if self.keepalive_timer <= 0:
                self.send_keepalive(
                self.keepalive_timer = 2700)
            '''
            try:
                if self.legacy_mode:
                    chunk = self.sock.recv(8192)
                    if not chunk:
                        break
                    self._read_legacy_chunk(chunk)
                else:
                    header = self._recv_exact(4)
                    if not header:
                        break
                    self.read_packet(header)

            except socket.timeout:
                continue

            except OSError as e:
                self.error.emit(str(e))
                break

    def send_packet(self, payload):
        if self.legacy_mode:
            return
        self.sock.sendall(makeAIOpacket(payload))

    def request_server_list(self):
        if self.legacy_mode:
            self._send_legacy("12#%")
            return
        self.send_packet(struct.pack("B", aio_protocol.MS_LIST))

    '''
    Sending impromper keepalives as client WILL crash the 2.0 masterserver.
    This needs to be redone to keep connection alive but idk how.

    def send_keepalive(self):
        if self.legacy_mode:
            self._send_legacy("KEEPALIVE#%")
            return
        self.send_packet(struct.pack("B", aio_protocol.MS_KEEPALIVE))
    '''

    def request_news(self):
        if self.legacy_mode:
            self._send_legacy("NEWS#%")
            return
        self.send_packet(struct.pack("B", aio_protocol.MS_NEWS))

    def read_packet(self, header):
        length, compression = readAIOheader(header)
        data = self._recv_exact(length)
        if not data:
            return

        if compression == 1:
            try:
                data = zlib.decompress(data)
            except zlib.error as e:
                self.error.emit(f"MasterServer decompress failed: {e}")
                return

        data, packet = buffer_read("B", data)
        if packet == aio_protocol.MS_CONNECTED:
            self.request_server_list()

        elif packet == aio_protocol.MS_LIST:
            data, amount = buffer_read("H", data)
            servers = []
            for _ in range(amount):
                data, ip = unpackString8(data)
                data, port = buffer_read("H", data)
                servers.append({"ip": ip, "port": port})
            self.serversReceived.emit(servers)

        elif packet == aio_protocol.MS_NEWS:
            data, news = unpackString16(data)
            self.newsReceived.emit(news)

    def _recv_exact(self, size):
        chunks = []
        remaining = size
        while remaining > 0:
            chunk = self.sock.recv(remaining)
            if not chunk:
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _send_legacy(self, text):
        try:
            self.sock.sendall(text.encode("utf-8"))
        except OSError as e:
            self.error.emit(str(e))

    def _read_legacy_chunk(self, chunk):
        self.legacy_buffer += chunk.decode("utf-8", errors="ignore")
        while "%" in self.legacy_buffer:
            frame, self.legacy_buffer = self.legacy_buffer.split("%", 1)
            frame = frame.strip()
            if frame:
                self._handle_legacy_frame(frame)

    #im going to end it
    def _handle_legacy_frame(self, frame):
        parts = frame.split('#')
        header = parts[0]
        fields = parts[1:]

        if header == "1":
            self.request_server_list()
            return
        if header == "12":
            servers = self._parse_legacy_servers(fields)
            self.serversReceived.emit(servers)
            return
        if header == "NEWS":
            news = fields[0] if fields else ""
            self.newsReceived.emit(news)
            return

        if header == "OKNOBO":
            reason = fields[1] if len(fields) > 1 else "Legacy masterserver error"
            self.error.emit(reason)
            return

        # debug
        self.error.emit(f"Error! Frame: {frame}")

    def _parse_legacy_servers(self, fields):

        if not fields:
            return []
        if fields [0] == "No servers online":
            return []

        fields = [f for f in fields if f != ""]

        servers = []
        for i in range(0, len(fields), 4):
            if i + 3 >=len(fields):
                break
            name = fields[i]
            desc = fields[i+1]
            ip = fields[i+2]
            port_raw = fields[i+3]
            try:
                port = int(port_raw)
            except ValueError:
                continue

            servers.append({
                "name": name,
                "description": desc,
                "ip": ip,
                "port": port,
                "version": "Legacy"
            })

        return servers
        
    def stop(self):
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        self.sock.close()
        self.wait()