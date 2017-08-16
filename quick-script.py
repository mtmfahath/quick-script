from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import pkgutil
import importlib
import json

class Window(QtWidgets.QMainWindow):
    def __init__(self, module_storage):
        self.module_storage = module_storage
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(390, 450)
        self.setStyleSheet("QWidget {color: #b1b1b1; background-color: #323232; border: 0px;}")
        self.centralwidget = QtWidgets.QWidget(self)

        # Search bar setup
        self.searchBar = QtWidgets.QLineEdit(self.centralwidget)
        self.searchBar.setGeometry(QtCore.QRect(5, 5, 281, 40))
        self.searchBar.setStyleSheet("background: transparent; padding-left: 8px; color: white; font: 15pt; border: 1px solid #ffffff;")
        self.searchBar.setPlaceholderText("Search")

        # Close button setup
        icon = QtGui.QPixmap('images/close.png')
        icon = icon.scaled(40, 40, QtCore.Qt.KeepAspectRatio)
        self.closeLabel = self.setup_static_button(QtCore.QRect(345, 5, 40, 40), icon)
        self.closeLabel.mousePressEvent = self.closeButtonAction

        # Settings button setup
        icon = QtGui.QPixmap('images/settings.png')
        icon = icon.scaled(30, 30, QtCore.Qt.KeepAspectRatio)
        self.settingsLabel = self.setup_static_button(QtCore.QRect(295, 5, 40, 40), icon)
        self.settingsLabel.mousePressEvent = self.settingsButtonAction

        # Scroll area setup
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(0, 50, 391, 401))
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet("""QScrollArea {border: 0px;}""")
        self.form = QtWidgets.QFormLayout()

        # Adding dynamic labels
        files = [i for i in self.module_storage]
        self.file_labels = {}
        for file in files:
            self.file_labels[file] = self.setup_dynamic_label(self.module_storage[file])
            self.form.addRow(self.file_labels[file])

        # Grouping
        self.groupbox = QtWidgets.QGroupBox()
        self.groupbox.setLayout(self.form)
        self.scrollArea.setWidget(self.groupbox)
        self.setCentralWidget(self.centralwidget)

    def setup_static_button(self, position, icon):
        tmp_label = QtWidgets.QLabel(self.centralwidget)
        tmp_label.setGeometry(position)
        tmp_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        tmp_label.setStyleSheet("QLabel {border: 1px solid #ffffff; font: 11pt; color: white;} QLabel:hover {border: 2px solid #ffaa00; color: #ffaa00;}")
        tmp_label.setPixmap(icon)
        tmp_label.setAlignment(QtCore.Qt.AlignCenter)
        return tmp_label

    def setup_dynamic_label(self, module):
        # TODO Check module has all four elements or print "Error in file: <filename>"
        tmp_label = QtWidgets.QLabel()
        tmp_label.setText(module.NAME)
        tmp_label.setStyleSheet("""QLabel {border: 1px solid #ffffff; font: 10pt; color: white;} QLabel:hover {border: 2px solid #ffaa00; color: #ffaa00;}""")
        tmp_label.setAlignment(QtCore.Qt.AlignCenter)
        tmp_label.setWordWrap(True)
        tmp_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        tmp_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        tmp_label.setToolTip("Runs: 0\nTags: " + str(module.TAGS) + "\nDescription: " + module.DESCRIPTION)
        tmp_label.setFixedHeight(40)
        tmp_label.setFixedWidth(self.width() - 20)
        tmp_label.mousePressEvent = self.labelClickEvent
        return tmp_label

    def closeButtonAction(self, event):
        if event.button() == 1:
            self.close()

    def settingsButtonAction(self, event):
        pass

    def labelClickEvent(self, event):
        if event.button() == 1:
            widgets = self.groupbox.children()
            for widget in widgets:
                hasGeo = getattr(widget, "mapToGlobal", None)
                if not callable(hasGeo):
                    continue
                if widget.mapToGlobal(event.pos()) == event.globalPos():
                    break
            name = widget.text()

            label_text_to_file_name = [i for i in self.module_storage if self.module_storage[i].NAME == name][0]

            if callable(getattr(self.module_storage[label_text_to_file_name], "main", None)):
                self.module_storage[label_text_to_file_name].main()
                if getSettings()["close_on_run"]:
                    self.close()
            else:
                print ("Error in file: " + self.module_storage[label_text_to_file_name].MODULE_FILE_NAME + "\nNo main() method found to run")


def getSettings():
    with open('settings.json') as data_file:
        return json.load(data_file)

def setSettings(data):
    try:
        with open('settings.json', 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)
        return True
    except:
        return False


if __name__ == "__main__":
    module_index = [name for _, name, _ in pkgutil.iter_modules(['scripts'])]
    module_storage = {}
    for module in module_index:
        module_storage[module] = importlib.import_module("scripts." + module)
        module_storage[module].MODULE_FILE_NAME = module + ".py"

    app = QtWidgets.QApplication(sys.argv)
    window = Window(module_storage)
    window.show()
    sys.exit(app.exec_())
