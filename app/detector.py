import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

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


class YOLODetector:
    """Ultralytics YOLO11n loader. If unavailable, returns empty detections."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        person_class_id: int = 0,
        conf: float = 0.35,
        max_det: int = 5,
        half: bool = True,
        imgsz: int = 480,
    ):
        self.person_class_id = person_class_id
        self.conf = conf
        self.max_det = max_det
        self.half = half
        self.model_path = model_path or "yolo11n.pt"
        self.imgsz = imgsz
        self.model = None
        self._load()

    def _load(self) -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as exc:  # pragma: no cover
            log.warning("Ultralytics not available: %s. Detector will be dummy.", exc)
            self.model = None
            return

        log.info("Loading YOLO model from %s", self.model_path)
        self.model = YOLO(self.model_path)

    def __call__(self, frame: np.ndarray) -> List[Detection]:
        if self.model is None:
            return []

        results = self.model(
            frame,
            verbose=False,
            conf=self.conf,
            half=self.half,
            max_det=self.max_det,
            imgsz=self.imgsz,
        )
        dets: List[Detection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                if cls_id != self.person_class_id:
                    continue
                conf = float(box.conf[0].item())
                if conf < self.conf:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                dets.append(Detection((x1, y1, x2, y2), conf, cls_id))
        return dets
