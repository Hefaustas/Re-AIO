import os
from configparser import ConfigParser
from turtle import down

from PySide6 import QtCore, QtGui, QtWidgets   
from signal import signal
from functools import partial

def getControlName(key):
    try:
        if key is None or key < 0:
            return "Unbound"
        seq = QtGui.QKeySequence(key)
        text = seq.toString(QtGui.QKeySequence.NativeText)
        if text:
            return text
        text = seq.toString()
        return text if text else f"Key({key})"
    except Exception:
        return f"Key({key})"

# used for rendering HTML in QListWidget
class HTMLDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc = QtGui.QTextDocument(self)

    def paint(self, painter, option, index):
        painter.save()
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        self.doc.setHtml(opt.text)
        opt.text = ""

        style = QtWidgets.QApplication.style() if opt.widget is None else opt.widget.style()
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, opt, painter)

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        if option.state & QtWidgets.QStyle.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.Text,
                                 option.palette.color(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
        else:
            ctx.palette.setColor(QtGui.QPalette.Text,
                                 option.palette.color(QtGui.QPalette.Active, QtGui.QPalette.Text))

        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, opt, opt.widget)
        margin = max(0, (option.rect.height() - opt.fontMetrics.height()) // 2)
        textRect.setTop(textRect.top() + margin)

        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        avail_width = option.rect.width() if option.rect.width() > 0 else 300
        self.doc.setTextWidth(avail_width)
        h = int(self.doc.size().height()) + 6
        return QtCore.QSize(avail_width, max(24, h))


class Options(QtWidgets.QWidget):
    # python3 equivalent for fileSaved = QtCore.pyqtSignal()
    #fileSaved = signal()

    def __init__(self, ao_app):
        super().__init__()
        self.ao_app = ao_app

        self.inifile = ConfigParser()
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 400)

        main_layout = QtWidgets.QVBoxLayout(self)
        save_layout = QtWidgets.QHBoxLayout()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.resize(320-16, 480-40)
        self.tabs.move(8, 8)

        general_tab = QtWidgets.QWidget()
        controls_tab = QtWidgets.QWidget()
        audio_tab = QtWidgets.QWidget()
        theme_tab = QtWidgets.QWidget()
        advanced_tab = QtWidgets.QWidget()

        general_layout = QtWidgets.QVBoxLayout(general_tab)
        general_layout.setAlignment(QtCore.Qt.AlignTop)

        controls_layout = QtWidgets.QVBoxLayout(controls_tab)
        controls_layout.setAlignment(QtCore.Qt.AlignTop)

        # use a QFormLayout for label/field rows
        audio_layout = QtWidgets.QFormLayout()
        audio_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        audio_layout.setFormAlignment(QtCore.Qt.AlignTop)
        audio_tab.setLayout(audio_layout)

        theme_layout = QtWidgets.QVBoxLayout(theme_tab)
        theme_layout.setAlignment(QtCore.Qt.AlignTop)

        advanced_layout = QtWidgets.QVBoxLayout(advanced_tab)
        advanced_layout.setAlignment(QtCore.Qt.AlignTop)

        savebutton = QtWidgets.QPushButton("Save")
        savebutton.clicked.connect(self.on_save_click)
        cancelbutton = QtWidgets.QPushButton("Cancel")
        cancelbutton.clicked.connect(self.on_cancel_click)

        separators = []
        for i in range(2):
            separator = QtWidgets.QFrame()
            separator.setFixedSize(separator.size().width(), 16)
            separators.append(separator)

        # General Tab
        defaultoocname_layout = QtWidgets.QHBoxLayout()
        defaultoocname_label = QtWidgets.QLabel("Default OOC Name")
        self.defaultoocname_textbox = QtWidgets.QLineEdit()
        defaultoocname_layout.addWidget(defaultoocname_label)
        defaultoocname_layout.addWidget(self.defaultoocname_textbox)

        defaultshowname_layout = QtWidgets.QHBoxLayout()
        defaultshowname_label = QtWidgets.QLabel("Default Showname")
        self.defaultshowname_textbox = QtWidgets.QLineEdit()
        defaultshowname_layout.addWidget(defaultshowname_label)
        defaultshowname_layout.addWidget(self.defaultshowname_textbox)  

        general_layout.addLayout(defaultoocname_layout)
        general_layout.addLayout(defaultshowname_layout)

        # Theme Tab
        themeview_layout = QtWidgets.QHBoxLayout()
        self.themeview = QtWidgets.QListWidget()
        self.themeview.setIconSize(QtCore.QSize(96, 96))
        self.themeview.setMovement(QtWidgets.QListView.Static)
        self.themeview.setItemDelegate(HTMLDelegate(self.themeview))

        self.themes = []
        for theme in os.listdir("data/themes"):
            if not os.path.exists(f"data/themes/{theme}/theme.ini"):
                continue

            self.inifile.read(f"data/themes/{theme}/theme.ini", encoding="utf-8")
            themename = self.inifile.get("Theme", "name", fallback=theme)
            themedesc = self.inifile.get("Theme", "description", fallback="No description available.")
            themeauthor = self.inifile.get("Theme", "author", fallback="Unknown")

            thumbnail = f"data/themes/{theme}/thumbnail.png"
            if not os.path.exists(thumbnail):
                thumbnail = "data/misc/unknown_theme.png"

            text = f"<b>{themename}</b><br><i>by {themeauthor}</i><br>{themedesc}"

            item = QtWidgets.QListWidgetItem(QtGui.QIcon(thumbnail), text)
            self.themes.append((theme, item))
            self.themeview.addItem(item)

        themeview_layout.addWidget(self.themeview)

        theme_layout.addLayout(themeview_layout)

        # Controls Tab
        self.changing_bind = []

        up_layout = QtWidgets.QHBoxLayout()
        up_label = QtWidgets.QLabel("Up")
        self.up_buttons = [QtWidgets.QPushButton(), QtWidgets.QPushButton()]

        down_layout = QtWidgets.QHBoxLayout()
        down_label = QtWidgets.QLabel("Down")
        self.down_buttons = [QtWidgets.QPushButton(), QtWidgets.QPushButton()]

        left_layout = QtWidgets.QHBoxLayout()
        left_label = QtWidgets.QLabel("Left")
        self.left_buttons = [QtWidgets.QPushButton(), QtWidgets.QPushButton()]

        right_layout = QtWidgets.QHBoxLayout()
        right_label = QtWidgets.QLabel("Right")
        self.right_buttons = [QtWidgets.QPushButton(), QtWidgets.QPushButton()]

        run_layout = QtWidgets.QHBoxLayout()
        run_label = QtWidgets.QLabel("Run")
        self.run_button = QtWidgets.QPushButton()

        for idx, b in enumerate(self.up_buttons):
            b.clicked.connect(partial(self.change_bind, b, "up", idx))
        for idx, b in enumerate(self.down_buttons):
            b.clicked.connect(partial(self.change_bind, b, "down", idx))
        for idx, b in enumerate(self.left_buttons):
            b.clicked.connect(partial(self.change_bind, b, "left", idx))
        for idx, b in enumerate(self.right_buttons):
            b.clicked.connect(partial(self.change_bind, b, "right", idx))
        self.run_button.clicked.connect(partial(self.change_bind, self.run_button, "run", 0))


        if os.path.exists("aaio.ini"):
            self.inifile.read("aaio.ini")
            for i in range(len(self.up_buttons)):
                ao_app.controls["up"][i] = self.inifile.getint("Controls", f"up{i+1}", fallback=ao_app.controls["up"][i])
            for i in range(len(self.down_buttons)):
                ao_app.controls["down"][i] = self.inifile.getint("Controls", f"down{i+1}", fallback=ao_app.controls["down"][i])
            for i in range(len(self.left_buttons)):
                ao_app.controls["left"][i] = self.inifile.getint("Controls", f"left{i+1}", fallback=ao_app.controls["left"][i])
            for i in range(len(self.right_buttons)):
                ao_app.controls["right"][i] = self.inifile.getint("Controls", f"right{i+1}", fallback=ao_app.controls["right"][i])
            ao_app.controls["run"][0] = self.inifile.getint("Controls", "run", fallback=ao_app.controls["run"][0])
        else:
            pass

        up_layout.addWidget(up_label)
        for b in self.up_buttons:
            up_layout.addWidget(b)
        down_layout.addWidget(down_label)
        for b in self.down_buttons:
            down_layout.addWidget(b)
        left_layout.addWidget(left_label)
        for b in self.left_buttons:
            left_layout.addWidget(b)
        right_layout.addWidget(right_label)
        for b in self.right_buttons:
            right_layout.addWidget(b)

        run_layout.addWidget(run_label)
        run_layout.addWidget(self.run_button)

        controls_layout.addLayout(up_layout)
        controls_layout.addLayout(down_layout)
        controls_layout.addLayout(left_layout)
        controls_layout.addLayout(right_layout)
        controls_layout.addLayout(run_layout)

        # Audio Tab
        device_label = QtWidgets.QLabel("Audio Device")
        self.device_list = QtWidgets.QComboBox()
        audio_layout.addRow(device_label, self.device_list)
        audio_layout.addRow(separators[0])

        sfx_label = QtWidgets.QLabel("Sound Effects")
        self.music_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.music_slider.setRange(0, 100)

        music_label = QtWidgets.QLabel("Music")
        self.sound_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.sound_slider.setRange(0, 100)

        blips_label = QtWidgets.QLabel("Blips")
        self.blips_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.blips_slider.setRange(0, 100)

        audio_layout.addRow(sfx_label, self.sound_slider)
        audio_layout.addRow(music_label, self.music_slider)
        audio_layout.addRow(blips_label, self.blips_slider)

        # your audio.getdevices() returns a list of names (or (id,name) tuples)
        try:
            devices = self.ao_app.audio.getdevices()
        except Exception:
            devices = []
        for d in devices:
            if isinstance(d, (list, tuple)) and len(d) >= 2:
                self.device_list.addItem(str(d[1]), d[0])
            else:
                self.device_list.addItem(str(d))

        # Advanced Tab
        ms_label = QtWidgets.QLabel("Master Server")
        ms_layout = QtWidgets.QHBoxLayout()
        self.ms_lineedit = QtWidgets.QLineEdit()

        ms_layout.addWidget(ms_label)
        ms_layout.addWidget(self.ms_lineedit)

        self.fps_checkbox = QtWidgets.QCheckBox("60 FPS mode", self)

        advanced_layout.addLayout(ms_layout)
        advanced_layout.addWidget(separators[1])
        advanced_layout.addWidget(self.fps_checkbox)


        self.tabs.addTab(general_tab, "General")
        self.tabs.addTab(theme_tab, "Theme")
        self.tabs.addTab(controls_tab, "Controls")
        self.tabs.addTab(audio_tab, "Audio")
        self.tabs.addTab(advanced_tab, "Advanced")

        save_layout.addWidget(savebutton, 100, alignment=QtCore.Qt.AlignRight)
        save_layout.addWidget(cancelbutton, 0, alignment=QtCore.Qt.AlignRight)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(save_layout)

        ao_app.installEventFilter(self)
        self.hide()

    def change_bind(self):
        pass

    def on_save_click(self):
        pass

    def on_cancel_click(self):
        self.hide()
        pass

    def eventFilter(self, source, event):
        if self.tabs.currentIndex() == 2 and self.changing_bind and event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key != QtCore.Qt.Key_Escape:
                self.ao_app.controls[self.changing_bind[1]][self.changing_bind[2]] = key
                self.changing_bind[0].setText(getControlName(key))
            else:
                self.changing_bind[0].setText(getControlName(self.ao_app.controls[self.changing_bind[1]][self.changing_bind[2]]))
            self.changing_bind = []
            return True
        return super(Options, self).eventFilter(source, event)


