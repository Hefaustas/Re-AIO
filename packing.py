import struct
import zlib


#mostly stolen, but tried cleaning some things up
def buffer_read(format, data):
    unpacked = struct.unpack_from(format, data)[0]
    size = struct.calcsize(format)
    return data[size:], unpacked

def readAIOheader(data):
    packet_size = struct.unpack("<I", data[:3] + b"\x00")[0]
    compression = data[3]
    return packet_size, compression

def makeAIOpacket(data, compression=0):
    if compression == 1:
        data = zlib.compress(data)
    finaldata = struct.pack("<I", len(data))[:3]
    finaldata += struct.pack("B", compression)
    return finaldata + data

def packString8(string):
    if isinstance(string, str):
        string = string.encode("utf-8")
    string = string[:255]
    return struct.pack(f"B{len(string)}s", len(string), string)

def packString16(string):
    if isinstance(string, str):
        string = string.encode("utf-8")
    string = string[:65535]
    return struct.pack(f"H{len(string)}s", len(string), string)

def unpackString8(data):
    length = struct.unpack_from("B", data)[0]
    start = 1
    end = start + length
    string = data[start:end].decode("utf-8")
    return data[end:], string

def unpackString16(data):
    length = struct.unpack_from("H", data)[0]
    start = 2
    end = start + length
    string = data[start:end].decode("utf-8")
    return data[end:], string

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