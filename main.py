from application import Application
import audio 

audio.init()
app = Application()

app.exec()
audio.free()