from PyQt5 import uic
from PyQt5.QtWidgets import (
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
)


class MainWindowView:

    def __init__(self) -> None:
        self.__ui: QMainWindow = uic.loadUi("v2img/view.ui")
        self.targetVideoGroupBox: QGroupBox = self.__ui.targetVideoGroupBox

        self.openVideoButton: QPushButton = self.__ui.openVideoButton
        self.videoPathLineEdit: QLineEdit = self.__ui.videoPathLineEdit

        self.codecLabel: QLabel = self.__ui.codecLabel
        self.fpsLabel: QLabel = self.__ui.fpsLabel
        self.frameSizeLabel: QLabel = self.__ui.frameSizeLabel

        self.frameSettingsGroupBox: QGroupBox = self.__ui.frameSettingsGroupBox

        self.openSavedirButton: QPushButton = self.__ui.openSavedirButton
        self.savedirPathLineEdit: QLineEdit = self.__ui.savedirPathLineEdit

        self.timeFromLineEdit: QLineEdit = self.__ui.timeFromLineEdit
        self.timeToLineEdit: QLineEdit = self.__ui.timeToLineEdit
        self.timeResetButton: QPushButton = self.__ui.timeResetButton

        self.doCompressRadio: QRadioButton = self.__ui.doCompressRadio
        self.noCompressRadio: QRadioButton = self.__ui.noCompressRadio
        self.jpegQualityLineEdit: QLineEdit = self.__ui.jpegQualityLineEdit

        self.saveFramesButton: QPushButton = self.__ui.saveFramesButton

    @property
    def window(self) -> QMainWindow:
        return self.__ui

    def show(self) -> None:
        self.__ui.show()

        self.__handler = self.__ui.windowHandle()
        self.__base_dpi = self.__handler.screen().logicalDotsPerInch()
        self.__base_width = self.__ui.width()
        self.__base_height = self.__ui.height()

        self.__handler.screenChanged.connect(self.__adjust_windowsize_for_dpi)
        self.__adjust_windowsize_for_dpi()

    def __adjust_windowsize_for_dpi(self) -> None:
        dpi = self.__handler.screen().logicalDotsPerInch() / self.__base_dpi
        new_width = int(self.__base_width * dpi)
        new_height = int(self.__base_height * dpi)

        self.__ui.setMinimumSize(new_width, new_height)
        self.__ui.setMaximumSize(new_width, new_height)
        self.__ui.resize(new_width, new_height)
        self.__ui.setFixedSize(new_width, new_height)
