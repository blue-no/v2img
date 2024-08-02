import sys

from PyQt5 import QtWidgets

from v2img.controller import MainWindowController
from v2img.view import MainWindowView

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    view = MainWindowView()
    ctrl = MainWindowController(app=app, view=view)
    ctrl.run()
    ctrl.clear()
