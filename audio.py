# platform-dependent audio handling using BASS, basically stolen from the old AIO
# modified to use pybass3 for 64-bit compatibility

# TODO: pybass3 doesn't support plugin loading, so OPUS support is dead currently. Need to figure out solution. Probably ctypes?
import platform, ctypes, os
from pybass_constants import *
from configparser import ConfigParser
dll = None
dllf = ""
opus = ""
use_pybass3 = False
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
    if not two: return opus
    return ""


def _pybass_helpers():
    import pybass3.bass_module as bass_module
    from pybass3.bass_module import Bass, func_type
    from pybass3.bass_channel import BassChannel
    from pybass3.bass_stream import BassStream
    return bass_module, Bass, BassChannel, BassStream, func_type


def init(freq=48000):
    """
Initialize BASS and the opus plugin
    """
    global dll, use_ctypes, use_pybass3
    if not dll:
        if platform.system() == "Darwin":
            dll = ctypes.CDLL(dllf)
            use_ctypes = True
        else:
            import pybass3 as dll
            use_pybass3 = True

    config = ConfigParser()
    config.read("re-aio.ini")

    if use_pybass3:
        _, Bass, _, _, func_type = _pybass_helpers()
        Bass.Init(config.getint("Audio", "device_index", fallback=-1), freq, 0, 0, 0)
        try:
            bass_module, _, _, _, func_type = _pybass_helpers()
            BASS_PluginLoad = func_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong)(('BASS_PluginLoad', bass_module.bass_module))
            BASS_PluginLoad(os.path.abspath(opus).encode('utf-8'), 0)
        except Exception:
            pass
    else:    
        dll.BASS_Init(config.getint("Audio", "device_index", fallback=-1), freq, 0, 0, 0)
        dll.BASS_PluginLoad(os.path.abspath(opus), 0)
    

def free():
    """
Free BASS
    """
    if use_pybass3:
        _, Bass, _, _, _ = _pybass_helpers()
        Bass.Free()
        return
    dll.BASS_Free()

def getcurrdevice():
    if use_pybass3:
        _, Bass, _, _, _ = _pybass_helpers()
        return Bass.GetCurrentDeviceID()
    return dll.BASS_GetDevice()

def getdevices():
    devices = []
    i = 0

    if use_pybass3:
        _, Bass, _, _, _ = _pybass_helpers()
        while True:
            try:
                info = Bass.GetDeviceInfo(i)
            except Exception:
                break
            name = info.name.decode("utf-8", errors="replace") if isinstance(info.name, bytes) else str(info.name)
            devices.append((i, name))
            i += 1
        return devices

    info = BASS_DEVICEINFO()
    if use_ctypes:
        while dll.BASS_GetDeviceInfo(i, ctypes.byref(info)):
            name = info.name.decode("utf-8", errors="replace") if isinstance(info.name, bytes) else str(info.name)
            devices.append((i, name))
            i += 1
        return devices

    while dll.BASS_GetDeviceInfo(i, info):
        name = info.name.decode("utf-8", errors="replace") if isinstance(info.name, bytes) else str(info.name)
        devices.append((i, name))
        i += 1

    return devices

def loadhandle(mem, file, offset=0, length=0, flags=0):
    """
Load a BASS stream handle
    """
    if use_pybass3:
        from pybass3.bass_stream import BASS_StreamCreateFile
        if isinstance(file, str):
            file = file.encode('utf-8')
        file_ptr = ctypes.c_char_p(file)
        return BASS_StreamCreateFile(mem, file_ptr, QWORD(offset), QWORD(length), flags)
    return dll.BASS_StreamCreateFile(mem, file, QWORD(offset), QWORD(length), flags)

def loadURLhandle(url, offset=0, flags=0, proc=DOWNLOADPROC(), user=0):
    """
Load a BASS stream handle from a URL
    """
    if use_pybass3:
        bass_module, _, _, _, func_type = _pybass_helpers()
        BASS_StreamCreateURL = func_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module.bass_module))
        return BASS_StreamCreateURL(url.encode('utf-8') if isinstance(url, str) else url, offset, flags, proc, user)
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
    if use_pybass3:
        bass_module, _, _, _, func_type = _pybass_helpers()
        BASS_MusicFree = func_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_MusicFree', bass_module.bass_module))
        return BASS_MusicFree(handle)
    return dll.BASS_MusicFree(handle)

def freehandle(handle):
    """
Free a handle
    """
    if use_pybass3:
        from pybass3.bass_stream import BassStream
        return BassStream.Free(handle)
    return dll.BASS_StreamFree(handle)

def playhandle(handle, restart):
    """
Play a handle
    """
    if use_pybass3:
        from pybass3.bass_channel import BassChannel
        return BassChannel.Play(handle, restart)
    return dll.BASS_ChannelPlay(handle, restart)

def stophandle(handle):
    """
Stop a handle
    """
    if use_pybass3:
        from pybass3.bass_channel import BassChannel
        return BassChannel.Stop(handle)
    return dll.BASS_ChannelStop(handle)

def handleisactive(handle):
    """
Get handle playback status
    """
    if use_pybass3:
        from pybass3.bass_channel import BassChannel
        return BassChannel.IsActive(handle)
    return dll.BASS_ChannelIsActive(handle)

def sethandleattr(handle, attr, value):
    """
Set an attribute for a handle
    """
    if use_pybass3:
        bass_module, _, _, _, func_type = _pybass_helpers()
        BASS_ChannelSetAttribute = func_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float)(('BASS_ChannelSetAttribute', bass_module.bass_module))
        return BASS_ChannelSetAttribute(handle, attr, ctypes.c_float(value) if isinstance(value, float) else value)
    if use_ctypes and type(value) == float: 
        value = ctypes.c_float(value)
    return dll.BASS_ChannelSetAttribute(handle, attr, value)
