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
        use_fallback: bool = True,
        fallback_model: str = "cnn",
        fallback_upsample: int = 2,
        fallback_resize_width: int = 0,
    ):
        self.model = model
        self.upsample = upsample
        self.resize_width = resize_width
        self.use_fallback = use_fallback
        self.fallback_model = fallback_model
        self.fallback_upsample = fallback_upsample
        self.fallback_resize_width = fallback_resize_width
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

        dets = self._detect(frame, model=self.model, upsample=self.upsample, resize_width=self.resize_width)

        # If nothing was found, try a slower but more accurate pass (e.g., CNN, no downscale)
        if not dets and self.use_fallback:
            dets = self._detect(
                frame,
                model=self.fallback_model,
                upsample=self.fallback_upsample,
                resize_width=self.fallback_resize_width if self.fallback_resize_width > 0 else 0,
            )

        return dets

    def _detect(self, frame: np.ndarray, model: str, upsample: int, resize_width: int) -> List[Detection]:
        # Optionally downscale to reduce load on Pi-class CPUs. resize_width==0 means full-res.
        scale = 1.0
        frame_in = frame
        if resize_width and frame.shape[1] > resize_width:
            scale = resize_width / frame.shape[1]
            new_h = max(1, int(frame.shape[0] * scale))
            frame_in = cv2.resize(frame, (resize_width, new_h))

        # face_recognition expects RGB images
        rgb = np.ascontiguousarray(frame_in[:, :, ::-1])
        boxes = self._face_recognition.face_locations(
            rgb, number_of_times_to_upsample=upsample, model=model
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
