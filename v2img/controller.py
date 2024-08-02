from itertools import zip_longest
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog

from v2img.model import FrameWriter, Video
from v2img.view import MainWindowView


class Initial:

    INFO = "-"
    TIMECODE = "00:00:00.000"
    JPEG_QUALITY = "85"


class MainWindowController:

    def __init__(
        self,
        app: QtWidgets.QApplication,
        view: MainWindowView,
    ) -> None:
        self.__app = app
        self.__view = view

        self.__video = None
        self.__writer = None

        view.openVideoButton.clicked.connect(self.__onOpenVideoButtonClicked)
        view.openSavedirButton.clicked.connect(
            self.__onOpenSavedirButtonClicked
        )
        view.timeFromLineEdit.editingFinished.connect(
            self.__onTimeFromLineEditEditingFinished
        )
        view.timeToLineEdit.editingFinished.connect(
            self.__onTimeToLineEditEditingFinished
        )
        view.timeResetButton.clicked.connect(self.__onTimeResetButtonClicked)
        view.doCompressRadio.clicked.connect(self.__onCompressRadioClicked)
        view.noCompressRadio.clicked.connect(self.__onCompressRadioClicked)
        view.jpegQualityLineEdit.editingFinished.connect(
            self.__onJpegQualityLineEditEditingFinished
        )
        view.saveFramesButton.clicked.connect(self.__onSaveFramesButtonClicked)

        posint_reg = QRegExp("^[0-9]*$")
        view.jpegQualityLineEdit.setValidator(QRegExpValidator(posint_reg))

        time_reg = QRegExp("^[0-9]*(?::[0-9]*)*\.?[0-9]*$")
        view.timeFromLineEdit.setValidator(QRegExpValidator(time_reg))
        view.timeToLineEdit.setValidator(QRegExpValidator(time_reg))

        view.frameSizeLabel.setText(Initial.INFO)
        view.codecLabel.setText(Initial.INFO)
        view.fpsLabel.setText(Initial.INFO)
        view.timeFromLineEdit.setText(Initial.TIMECODE)
        view.timeToLineEdit.setText(Initial.TIMECODE)
        view.jpegQualityLineEdit.setText(Initial.JPEG_QUALITY)

        view.frameSettingsGroupBox.setEnabled(False)
        view.saveFramesButton.setEnabled(False)

    def run(self) -> None:
        self.__view.show()
        _ = self.__app.exec_()

    def clear(self) -> None:
        if self.__video is not None:
            self.__video.close()

    def __onOpenVideoButtonClicked(self) -> None:
        suffs = " ".join(
            [
                (" *." + s).lower() + (" *." + s).upper()
                for s in Video.VideoFormat.list()
            ]
        )
        fp, _ = QFileDialog.getOpenFileName(
            parent=self.__view.window,
            caption="ファイルを選択",
            filter=f"Video Files ({suffs})",
        )
        if fp == "":
            return

        fp = Path(fp)
        self.__video = Video.read(fp)
        self.__view.videoPathLineEdit.setText(fp.as_posix())
        self.__view.codecLabel.setText(self.__video.codec)
        self.__view.fpsLabel.setText(str(self.__video.fps))
        self.__view.frameSizeLabel.setText(
            f"縦 {self.__video.frames.height} x 横 {self.__video.frames.width}"
        )
        self.__view.timeToLineEdit.setText(
            str(_seconds_to_timecode(self.__video.sec_length))
        )

        self.__view.frameSettingsGroupBox.setEnabled(True)

    def __onOpenSavedirButtonClicked(self) -> None:
        fp = QFileDialog.getExistingDirectory(
            parent=self.__view.window,
            caption="フォルダを選択",
        )
        if fp == "":
            return

        fp = Path(fp)
        self.__writer = FrameWriter(_savedir=fp)
        self.__view.savedirPathLineEdit.setText(fp.as_posix())

        self.__view.saveFramesButton.setEnabled(True)

    def __onTimeFromLineEditEditingFinished(self) -> None:
        timecode = _format_timecode(self.__view.timeFromLineEdit.text())
        if self.__video.sec_length < _timecode_to_seconds(timecode):
            timecode = _seconds_to_timecode(self.__video.sec_length)
        self.__view.timeFromLineEdit.setText(timecode)

    def __onTimeToLineEditEditingFinished(self) -> None:
        timecode = _format_timecode(self.__view.timeToLineEdit.text())
        if self.__video.sec_length < _timecode_to_seconds(timecode):
            timecode = _seconds_to_timecode(self.__video.sec_length)
        self.__view.timeToLineEdit.setText(timecode)

    def __onTimeResetButtonClicked(self) -> None:
        if self.__video is None:
            return
        self.__view.timeFromLineEdit.setText(Initial.TIMECODE)
        self.__view.timeToLineEdit.setText(
            _seconds_to_timecode(self.__video.sec_length)
        )

    def __onCompressRadioClicked(self) -> None:
        if self.__view.doCompressRadio.isChecked():
            self.__view.jpegQualityLineEdit.setEnabled(True)
        elif self.__view.noCompressRadio.isChecked():
            self.__view.jpegQualityLineEdit.setEnabled(False)

    def __onJpegQualityLineEditEditingFinished(self) -> None:
        text = self.__view.jpegQualityLineEdit.text()
        if text == "":
            rounded = 60
        else:
            value = int(text)
            rounded = max(min(value, 100), 60)
        self.__view.jpegQualityLineEdit.setText(str(rounded))

    def __onSaveFramesButtonClicked(self) -> None:
        self.__onJpegQualityLineEditEditingFinished()
        self.__onTimeFromLineEditEditingFinished()
        self.__onTimeToLineEditEditingFinished()
        sec_from = _timecode_to_seconds(self.__view.timeFromLineEdit.text())
        sec_to = _timecode_to_seconds(self.__view.timeToLineEdit.text())

        if sec_from >= sec_to:
            QMessageBox.warning(
                self.__view.window,
                "注意",
                "時間の始まりと終わりが逆転しています。",
                QMessageBox.Ok,
            )
            return

        if self.__view.doCompressRadio.isChecked():
            format_ = FrameWriter.ImageFormat.JPEG
        elif self.__view.noCompressRadio.isChecked():
            format_ = FrameWriter.ImageFormat.PNG
        else:
            raise NotImplementedError

        if self.__writer.savedir.glob(f"*.{format_}"):
            reply = QMessageBox.question(
                self.__view.window,
                "確認",
                "同じ名前の画像は上書きされます。処理を進めますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        jpeg_quality = int(self.__view.jpegQualityLineEdit.text())
        frames = self.__video.clip(sec_from=sec_from, sec_to=sec_to).frames
        ndigits = len(str(frames.range.stop))

        self.__view.window.setEnabled(False)
        try:
            progress_dialog = QProgressDialog(
                "保存中...",
                "キャンセル",
                frames.range.start,
                frames.range.stop - frames.range.step,
                self.__view.window,
            )
            progress_dialog.setFont(self.__view.window.font())
            progress_dialog.setMinimumDuration(1000)

            for frame, n in zip(frames.iterate(), frames.range):
                if progress_dialog.wasCanceled():
                    break

                self.__writer.write(
                    stem=str(n + 1).zfill(ndigits),
                    format_=format_,
                    img=frame,
                    jpeg_quality=jpeg_quality,
                )

                progress_dialog.setValue(n)
                self.__app.processEvents()

            else:
                QMessageBox.information(
                    self.__view.window,
                    "情報",
                    "完了しました。",
                    QMessageBox.Ok,
                )

        except Exception as e:
            QMessageBox.critical(
                self.__view.window,
                "エラー",
                f"予期せぬエラーが発生しました。\n{e}",
                QMessageBox.Ok,
            )

        finally:
            self.__view.window.setEnabled(True)
            progress_dialog.close()


def _format_timecode(timecode: str) -> str:
    tsegs = {"h": 0, "m": 0, "s": 0}

    over = 0
    for tseg, tcode in zip_longest(
        reversed(tsegs),
        reversed(timecode.split(":")[-3:]),
        fillvalue="",
    ):
        if tcode == "":
            tnum = over
        else:
            tnum = float(tcode) + over
        quo = tnum // 60
        rem = tnum % 60
        if tseg == "s":
            tsegs[tseg] += rem
        else:
            tsegs[tseg] += int(rem)
        over = quo

    return f'{tsegs["h"]:02}:{tsegs["m"]:02}:{tsegs["s"]:06.3f}'


def _timecode_to_seconds(timecode: str) -> float:
    try:
        hours, minutes, rest = timecode.split(":")
        seconds, milliseconds = rest.split(".")
    except ValueError:
        raise ValueError("Invalid time format. Expected hh:mm:ss.ms")

    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    total_seconds = (
        (hours * 3600) + (minutes * 60) + seconds + (milliseconds / 1000)
    )

    return total_seconds


def _seconds_to_timecode(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    timecode = f"{hours:02}:{minutes:02}:{sec:02}.{milliseconds:03}"

    return timecode
