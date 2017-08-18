from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import pkgutil
import importlib
import json
import inspect

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
        self.searchBar.setFocus()
        self.searchBar.textChanged.connect(self.search)

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

        # Adding dynamic labels # TODO Sort by runs
        files = [i for i in self.module_storage]
        self.file_labels = {}
        order_labels = []
        # Put files in a list of a pair [#, label]
        for file in files:
            self.file_labels[file] = self.setup_dynamic_label(self.module_storage[file])
            order_labels.append([self.getModuleRuns(self.file_labels[file].associated_module), self.file_labels[file]])

        # Order list by highest to lowest and add to display
        order_labels_sorted = sorted(order_labels, key=lambda x: x[0])[::-1]
        for label_pair in order_labels_sorted:
            self.form.addRow(label_pair[1])

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
        label_name, label_tooltip = self.getModuleContent(module)

        tmp_label = QtWidgets.QLabel()
        tmp_label.setStyleSheet("""QLabel {border: 1px solid #ffffff; font: 10pt; color: white;} QLabel:hover {border: 2px solid #ffaa00; color: #ffaa00;}""")
        tmp_label.setAlignment(QtCore.Qt.AlignCenter)
        tmp_label.setWordWrap(True)
        tmp_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        tmp_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        tmp_label.setFixedHeight(40)
        tmp_label.setFixedWidth(self.width() - 20)
        tmp_label.mousePressEvent = self.labelClickEvent
        tmp_label.setText(label_name)
        tmp_label.setToolTip(label_tooltip)
        tmp_label.associated_module = module

        return tmp_label

    def getModuleContent(self, module):
        if getattr(module, "NAME", False):
            label_name = module.NAME
        else:
            label_name = module.MODULE_FILE_NAME

        label_tooltip = "Runs: " + str(self.getModuleRuns(module))
        label_tooltip += "\nTags: " + str(getattr(module, "TAGS", "None"))
        label_tooltip += "\nDescription: " + getattr(module, "DESCRIPTION", "None")

        return label_name, label_tooltip

    def getModuleRuns(self, module):
        settings = getSettings()
        if module.MODULE_FILE_NAME in settings["run_count"]:
            return settings["run_count"][module.MODULE_FILE_NAME]
        else:
            settings["run_count"][module.MODULE_FILE_NAME] = 0
            setSettings(settings)
            return 0

    def addModuleRun(self, module):
        settings = getSettings()
        settings["run_count"][module.MODULE_FILE_NAME] += 1
        setSettings(settings)

    def closeButtonAction(self, event):
        if event.button() == 1:
            self.close()

    def settingsButtonAction(self, event):
        pass

    def labelClickEvent(self, event):
        if event.button() == 1:
            widgets = self.groupbox.findChildren(QtWidgets.QLabel)
            for widget in widgets:
                if widget.mapToGlobal(event.pos()) == event.globalPos():
                    break
            label = widget # label clicked (object)

            # Run main, display warning if not found
            if callable(getattr(label.associated_module, "main", None)):
                # Pass the current window to main if the main method takes on parameter
                if len(inspect.getargspec(label.associated_module.main).args) == 1:
                    label.associated_module.main(self)
                else:
                    label.associated_module.main()
                self.addModuleRun(label.associated_module)
                if getSettings()["close_on_run"]:
                    self.close()
            else:
                self.dialogCritical("No main()", "Error in file: " + label.associated_module.MODULE_FILE_NAME + "\nNo main() method found to run")

    def search(self, search_item):
        search_item = search_item.lower()

        if search_item == "": # No search
            for script in self.file_labels:
                self.file_labels[script].show()
        else: # Search
            terms = search_item.split(" ")
            for script in self.file_labels:
                search_match = False
                for term in terms:
                    if term in script + '.py':
                        search_match = True
                        break
                    if any([term in i.lower() for i in getattr(self.file_labels[script].associated_module, "TAGS", "")]):
                        search_match = True
                        break
                    if term in getattr(self.file_labels[script].associated_module, "DESCRIPTION", "").lower():
                        search_match = True
                        break
                    if term in getattr(self.file_labels[script].associated_module, "NAME", "").lower():
                        search_match = True
                        break
                if search_match:
                    self.file_labels[script].show()
                else:
                    self.file_labels[script].hide()

    def dialogCritical(self, title, message):
        msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, title, message, QtWidgets.QMessageBox.NoButton, self)
        msgBox.setStyleSheet("QPushButton { color: white; border: 1px solid #ffffff; padding: 7px;} QPushButton:hover {border: 1px solid #ffaa00; color: #ffaa00;}")
        msgBox.exec_()

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

