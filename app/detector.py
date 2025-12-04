import logging
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class Detection:
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    conf: float
    cls: int

    @property
    def center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return (x1 + x2) / 2, (y1 + y2) / 2


class FaceRecognitionDetector:
    """
    Face detector backed by https://github.com/ageitgey/face_recognition.
    If the dependency is missing, detection becomes a no-op.
    """

    def __init__(
        self,
        model: str = "hog",
        upsample: int = 1,
        resize_width: int = 320,
    ):
        self.model = model
        self.upsample = upsample
        self.resize_width = resize_width
        self._face_recognition = self._load()

    def _load(self):
        try:
            import face_recognition  # type: ignore
        except Exception as exc:  # pragma: no cover
            log.warning("face_recognition not available: %s. Detector will be dummy.", exc)
            return None

        return face_recognition

    def __call__(self, frame: np.ndarray) -> List[Detection]:
        if self._face_recognition is None:
            return []

        # Optionally downscale to reduce load on Pi-class CPUs
        scale = 1.0
        frame_in = frame
        if self.resize_width and frame.shape[1] > self.resize_width:
            scale = self.resize_width / frame.shape[1]
            new_h = max(1, int(frame.shape[0] * scale))
            frame_in = cv2.resize(frame, (self.resize_width, new_h))

        # face_recognition expects RGB images
        rgb = np.ascontiguousarray(frame_in[:, :, ::-1])
        boxes = self._face_recognition.face_locations(
            rgb, number_of_times_to_upsample=self.upsample, model=self.model
        )
        dets: List[Detection] = []
        for top, right, bottom, left in boxes:
            if scale != 1.0:
                top /= scale
                right /= scale
                bottom /= scale
                left /= scale
            dets.append(Detection((left, top, right, bottom), conf=1.0, cls=0))
        return dets
