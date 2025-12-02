import logging
import os
import platform
from typing import Optional, Tuple

import cv2
import numpy as np

log = logging.getLogger(__name__)


class Camera:
    """Thin wrapper around OpenCV VideoCapture with lazy open and backend fallbacks."""

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480, fps: int = 15):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self._candidates = self._build_candidates()
        self._cand_pos = 0
        self._read_failures = 0

    def _build_candidates(self):
        candidates = []
        if platform.system().lower() == "windows":
            os.environ.setdefault("OPENCV_VIDEOIO_MSMF_DISABLE", "1")
            os.environ.setdefault("OPENCV_VIDEOIO_PRIORITY_MSMF", "0")
            cam_name = os.environ.get("CAMERA_NAME")
            if cam_name:
                candidates.append((f"video={cam_name}", cv2.CAP_DSHOW))
            candidates.append((self.device_index, cv2.CAP_DSHOW))
            candidates.append((self.device_index, cv2.CAP_ANY))
        else:
            candidates.append((self.device_index, cv2.CAP_ANY))
        return candidates

    def open(self) -> None:
        if self.cap is not None:
            return
        for i in range(len(self._candidates)):
            target, backend = self._candidates[(self._cand_pos + i) % len(self._candidates)]
            log.info("Opening camera target=%s backend=%s", target, backend)
            cap = cv2.VideoCapture(target, backend)
            if cap.isOpened():
                self.cap = cap
                self._cand_pos = (self._cand_pos + i) % len(self._candidates)
                self._read_failures = 0
                break
            cap.release()
        if self.cap is None:
            raise RuntimeError(f"Cannot open camera (tried candidates for target={self.device_index})")
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
            self._read_failures += 1
            if self._read_failures >= 3:
                self._cand_pos = (self._cand_pos + 1) % len(self._candidates)
                self.release()
                try:
                    self.open()
                except Exception as exc:
                    log.error("Reopen camera failed: %s", exc)
            return None
        self._read_failures = 0
        return ret, frame

    def release(self) -> None:
        if self.cap:
            log.info("Releasing camera")
            self.cap.release()
            self.cap = None
