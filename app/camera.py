import logging
from typing import Optional, Tuple

import cv2
import numpy as np

log = logging.getLogger(__name__)


class Camera:
    """Thin wrapper around OpenCV VideoCapture with lazy open."""

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480, fps: int = 15):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        if self.cap is not None:
            return
        log.info("Opening camera index=%s", self.device_index)
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera index={self.device_index}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

    def read(self) -> Optional[Tuple[bool, np.ndarray]]:
        if self.cap is None:
            self.open()
        assert self.cap is not None
        ret, frame = self.cap.read()
        if not ret:
            log.warning("Camera read failed")
            return None
        return ret, frame

    def release(self) -> None:
        if self.cap:
            log.info("Releasing camera")
            self.cap.release()
            self.cap = None
