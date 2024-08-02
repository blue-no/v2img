from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from pathlib import Path

import cv2
import numpy as np


class FileFormat(Enum):

    @classmethod
    def as_suffix(cls, fmt: FileFormat) -> str:
        return "." + fmt.value

    @classmethod
    def list(cls) -> list[str]:
        return [e.value for e in cls]


class Video:

    class VideoFormat(FileFormat):
        AVI = "avi"
        MP4 = "mp4"
        MOV = "mov"
        MKV = "mkv"
        FLV = "flv"
        WMV = "wmv"
        WEBM = "webm"

    def __init__(self, frames: Frames, codec: str, fps: float) -> None:
        self.__frames = frames
        self.__codec = codec.lower()
        self.__fps = fps

    @property
    def frames(self) -> Frames:
        return self.__frames

    @property
    def codec(self) -> str:
        return self.__codec.upper()

    @property
    def fps(self) -> float:
        return self.__fps

    @property
    def sec_length(self) -> float:
        return self.__frames.count / self.__fps

    @classmethod
    def read(cls, fp: Path | str) -> Video:
        fp = Path(fp)
        if not fp.exists():
            raise FileNotFoundError
        cap = cv2.VideoCapture(fp.as_posix())

        return Video(
            frames=Frames(_cap=cap),
            codec="".join(
                [
                    chr((int(cap.get(cv2.CAP_PROP_FOURCC)) >> 8 * i) & 0xFF)
                    for i in range(4)
                ]
            ),
            fps=float(cap.get(cv2.CAP_PROP_FPS)),
        )

    def write(self, fp: Path | str) -> Video:
        fp = Path(fp)
        fp.mkdir(parents=True, exist_ok=True)

        writer = cv2.VideoWriter(
            filename=fp.as_posix(),
            fourcc=cv2.VideoWriter_fourcc(*self.__codec),
            fps=self.__fps,
            frameSize=(self.__frames.width, self.__frames.height),
        )

        try:
            for frame in self.__frames.iterate():
                writer.write(frame)
        finally:
            writer.release()

    def clip(
        self,
        sec_from: int | None = None,
        sec_to: int | None = None,
    ) -> Video:
        if sec_from is None:
            sec_from = 0
        elif sec_from < 0:
            raise ValueError

        if sec_to is None:
            sec_to = self.sec_length
        elif sec_to > self.sec_length:
            raise ValueError

        i_from = self.__frames.range.start + int(np.ceil(self.__fps * sec_from))
        i_to = self.__frames.range.start + int(np.floor(self.__fps * sec_to))

        return Video(
            frames=self.__frames.set_range(range(i_from, i_to)),
            codec=self.__codec,
            fps=self.__fps,
        )

    def close(self) -> None:
        self.__frames.release()


class Frames:

    def __init__(
        self,
        _cap: cv2.VideoCapture,
        _range: range | None = None,
    ) -> None:
        self.__cap = _cap
        _max_frame_index = int(_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if _range is None:
            self.__range = range(0, _max_frame_index)
            return

        if _range.start < 0 or _range.stop > _max_frame_index:
            raise ValueError("Invalid frame range.")
        if _range.start > _range.stop:
            raise ValueError("End time is before start time.")
        self.__range = _range

    @property
    def width(self) -> int:
        return int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self) -> int:
        return int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def count(self) -> int:
        return len(self.__range)

    @property
    def range(self) -> range:
        return self.__range

    def set_range(self, range_: range) -> Frames:
        return Frames(_cap=self.__cap, _range=range_)

    def iterate(self) -> Iterator[np.ndarray]:
        self.__cap.set(cv2.CAP_PROP_POS_FRAMES, self.__range.start)
        for _ in self.__range:
            success, frame = self.__cap.read()
            if not success:
                raise Exception("cv2.VideoCapture().read() failed.")
            yield frame
        return

    def release(self) -> None:
        self.__cap.release()


class FrameWriter:

    class ImageFormat(FileFormat):
        JPEG = "jpg"
        PNG = "png"
        BMP = "bmp"
        TIFF = "tif"

    def __init__(self, _savedir: Path | str) -> None:
        self.__savedir = Path(_savedir)

    @property
    def savedir(self) -> Path:
        return self.__savedir

    def write(
        self,
        stem: str,
        format_: ImageFormat,
        img: np.ndarray,
        jpeg_quality: int | None = None,
    ) -> None:
        if format_ == FrameWriter.ImageFormat.JPEG:
            if jpeg_quality is None:
                raise ValueError("'jpeg_quality' cannot be None.")
            params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        elif format_ == FrameWriter.ImageFormat.PNG:
            params = []
        elif format_ == FrameWriter.ImageFormat.TIFF:
            params = [cv2.IMWRITE_TIFF_COMPRESSION, 3]
        elif format_ == FrameWriter.ImageFormat.BMP:
            params = []

        suffix = FrameWriter.ImageFormat.as_suffix(format_)
        fp = self.__savedir.joinpath(stem).with_suffix(suffix)
        success, buffer = cv2.imencode(suffix, img, params=params)
        if not success:
            raise Exception("cv2.imencode() failed.")
        with fp.open("wb") as f:
            buffer.tofile(f)
