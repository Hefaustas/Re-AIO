import struct
import zlib


def buffer_read(format, data):
    unpacked = struct.unpack_from(format, data)
    size = struct.calcsize(format)
    return data[size:], unpacked[0]  # [size:] means skip ahead size amount of bytes


def readAIOHeader(data):
    if isinstance(data, str):
        data = data.encode("latin1")
    packetsize, = struct.unpack("I", data[:3] + b"\x00")  # read first 3 bytes. this is the packet size
    compression = data[3]  # the last byte is the compression type. 0=none, 1=zlib
    return packetsize, compression  # after that you do tcp.recv(packetsize) and check if decompression is needed


def readAIOheader(data):
    return readAIOHeader(data)


def makeAIOPacket(data, compression=0):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if compression == 1:
        data = zlib.compress(data)
    finaldata = struct.pack("I", len(data))[:3]  # strip the 4th byte off of it
    finaldata += struct.pack("B", compression)  # compression type
    return finaldata + data


def makeAIOpacket(data, compression=0):
    return makeAIOPacket(data, compression)


def packString8(string):
    if isinstance(string, bytes):
        string = string.decode("utf-8", errors="ignore")
    string = str(string)[:255]
    encoded = string.encode("utf-8")
    l = len(encoded)
    buf = struct.pack("B%ds" % l, l, encoded)
    return buf


def packString16(string):
    if isinstance(string, bytes):
        string = string.decode("utf-8", errors="ignore")
    string = str(string)[:65535]
    encoded = string.encode("utf-8")
    l = len(encoded)
    buf = struct.pack("H%ds" % l, l, encoded)
    return buf


def unpackString8(data):
    l, = struct.unpack_from("B", data)
    string, = struct.unpack_from("%ds" % l, data[1:])
    if isinstance(string, bytes):
        string = string.decode("utf-8", errors="ignore")
    return data[struct.calcsize("B%ds" % l):], string[:l]


def unpackString16(data):
    l, = struct.unpack_from("H", data)
    string, = struct.unpack_from("%ds" % l, data[2:])
    if isinstance(string, bytes):
        string = string.decode("utf-8", errors="ignore")
    return data[struct.calcsize("H%ds" % l):], string[:l]

def versionToInt(version):
    parts = version.split(".")
    major = parts[0]
    minor = parts[1]
    patch = parts[2] if len(parts) > 2 else "0" 
    try:
        return int(major + minor + patch)
    except ValueError:
        return int(major + minor + "0")

def versionToStr(version):
    if len(version) < 2:
        return version
    major = version[1]
    minor = version[0]
    if len(version) == 2:
        return f"{major}.{minor}"
    patch = version[2]
    return f"{major}.{minor}.{patch}"