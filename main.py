import traceback
from application import Application
import audio 

#my shit stopped printing the exceptions idk why
try:
    audio.init()
    app = Application()
    app.exec()
except Exception:
    traceback.print_exc()
    raise
finally:
    try:
        audio.free()
    except Exception:
        pass