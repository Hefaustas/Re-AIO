import socket
import struct
import time
import zlib

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QThread, Signal

from main_window import MainWindow
import aio_protocol
from packing import *
import audio

class Application(QApplication):
    player_id = -1
    charlist, musiclist, zonelist = [], [], []

    def __init__(self, argv=[]):
        super().__init__(argv)

        self.udpthread = UDPThread()
        self.udpthread.start()

        self.audio = audio

        self.controls = {
            "up": [Qt.Key_W, Qt.Key_Up],
            "down": [Qt.Key_S, Qt.Key_Down],
            "left": [Qt.Key_A, Qt.Key_Left],
            "right": [Qt.Key_D, Qt.Key_Right],
            "run": [Qt.Key_Shift, -1],
        }

        self.main_window = MainWindow(self)
        self.main_window.show()
        

class ClientThread:
    pass


class UDPThread(QThread):
    info_received = Signal(list)
    def __init__(self):
        super().__init__()
        self.udp = None
        self.running = True
        self.pings = {}

    def stop(self):
        self.running = False
        if self.udp is not None:
            self.udp.close()

        self.wait()

    def send_buffer(self, data, addr):
        host, port = addr
        self.udp.sendto(data, (host, int(port)))

    def send_info_request(self, addr):
        # addr = ip+port
        addr = (addr[0], int(addr[1]))
        self.pings[addr] = time.time()
        packet = struct.pack("B", aio_protocol.UDP_REQUEST)
        self.send_buffer(packet, addr)

    def run(self):
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp.settimeout(0.1)

        self.running = True

        while self.running:
            try:
                data, addr = self.udp.recvfrom(65535)

            except socket.timeout:
                continue

            except OSError as e:
                if not self.running:
                    break

                print(e)
                continue

            try:
                data = zlib.decompress(data)

            except zlib.error:
                continue

            data, header = buffer_read("B", data)

            if header != aio_protocol.UDP_REQUEST:
                continue

            data, name = unpackString16(data)
            data, description = unpackString16(data)
            data, players = buffer_read("I", data)
            data, max_players = buffer_read("I", data)
            data, version = buffer_read("H", data)
            ping = "999"

            sent_ping = addr in self.pings
            is_lan = False

            for server in self.pings:
                if server[0] == "<broadcast>" and server[1] == addr[1]:
                    sent_ping = True
                    is_lan = True
                    break

            addr_key = addr if not is_lan else ("<broadcast>", addr[1])

            if sent_ping:
                ping_before = self.pings[addr_key]
                ping_after = time.time()

                ping = str(int((ping_after - ping_before) * 1000))
                del self.pings[addr_key]

            self.info_received.emit([
                addr,
                name,
                description,
                players,
                max_players,
                version,
                ping
            ])