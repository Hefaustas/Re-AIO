# platform-dependent audio handling using BASS, basically stolen from the old AIO
# modified to use pybass3 for 64-bit compatibility

import platform, ctypes, os
from pybass_constants import *
from configparser import ConfigParser
dll = None
dllf = ""
opus = ""
use_ctypes = False
if platform.system() == "Windows":
    dllf = "bass.dll"
    opus = "bassopus.dll"
elif platform.system() == "Darwin":
    dllf = "libbass.dylib"
    opus = "libbassopus.dylib"
else:
    dllf = "libbass.so"
    opus = "libbassopus.so"

def checkAvailable():
    """
Check if the DLLs exist
Returns string with dll name if it's missing, empty if all DLLs are in place
    """
    one = os.path.exists(os.path.abspath(dllf))
    two = os.path.exists(os.path.abspath(opus))
    if not one: return dllf
    if not two: return two
    return ""

def init(freq=48000):
    """
Initialize BASS and the opus plugin
    """
    global dll, use_ctypes
    if not dll:
        if platform.system() == "Darwin":
            dll = ctypes.CDLL(dllf)
            use_ctypes = True
        else:
            import pybass3 as dll

    config = ConfigParser()
    config.read("re-aio.ini")
    dll.BASS_Init(config.getint("Audio", "device", -1), freq, 0, 0, 0)
    dll.BASS_PluginLoad(os.path.abspath(opus), 0)

def free():
    """
Free BASS
    """
    dll.BASS_Free()

def getcurrdevice():
    return dll.BASS_GetDevice()

def getdevices():
    """
Get BASS devices
    """
    info = BASS_DEVICEINFO() if use_ctypes else dll.BASS_DEVICEINFO()
    i = 0
    devices = []
    while dll.BASS_GetDeviceInfo(i, ctypes.c_voidp(ctypes.addressof(info)) if use_ctypes else info):
        devices.append(i, info.name)
        i += 1
    return devices

def loadhandle(mem, file, offset=0, length=0, flags=0):
    """
Load a BASS stream handle
    """
    return dll.BASS_StreamCreateFile(mem, file, QWORD(offset), QWORD(length), flags)

def loadURLhandle(url, offset=0, flags=0, proc=DOWNLOADPROC(), user=0):
    """
Load a BASS stream handle from a URL
    """
    return dll.BASS_StreamCreateURL(url, offset, flags, proc, user)

def loadmusic(mem, file, offset=0, length=0, flags=0):
    """
Load a MOD music file
    """
    return dll.BASS_MusicLoad(mem, file, QWORD(offset), QWORD(length), flags, 1)

def freemusic(handle):
    """
Free a MOD music handle from memory
    """
    return dll.BASS_MusicFree(handle)

def freehandle(handle):
    """
Free a handle
    """
    return dll.BASS_StreamFree(handle)

def playhandle(handle, restart):
    """
Play a handle
    """
    return dll.BASS_ChannelPlay(handle, restart)

def stophandle(handle):
    """
Stop a handle
    """
    return dll.BASS_ChannelStop(handle)

def handleisactive(handle):
    """
Get handle playback status
    """
    return dll.BASS_ChannelIsActive(handle)

def sethandleattr(handle, attr, value):
    """
Set an attribute for a handle
    """
    if use_ctypes and type(value) == float: 
        value = ctypes.c_float(value)
    return dll.BASS_ChannelSetAttribute(handle, attr, value)
