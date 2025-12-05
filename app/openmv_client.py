import logging
import os
import time
from typing import List, Optional, Tuple

import numpy as np
try:
    from serial.tools import list_ports
except Exception:  # pragma: no cover
    list_ports = None  # type: ignore

from .detector import Detection

log = logging.getLogger(__name__)

try:
    from . import pyopenmv
except Exception as exc:  # pragma: no cover
    pyopenmv = None  # type: ignore
    log.debug("pyopenmv not available: %s", exc)


DEFAULT_FACE_SCRIPT = """
import sensor, image, time

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.{framesize})
sensor.skip_frames(time=2000)
clock = time.clock()
face_cascade = image.HaarCascade("frontalface", stages=25)

while True:
    clock.tick()
    img = sensor.snapshot()
    faces = img.find_features(face_cascade, threshold={threshold}, scale={scale})
    out = []
    for f in faces:
        out.append("%d,%d,%d,%d" % (f[0], f[1], f[2], f[3]))
    print("FACES:" + "|".join(out))
"""


class OpenMVCamera:
    """
    Talks to an OpenMV camera over USB/serial using pyopenmv.
    The script running on the camera prints face bounding boxes, which we parse from the text buffer.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 921600,
        framesize: str = "QVGA",
        threshold: float = 0.7,
        scale: float = 1.35,
        timeout: float = 0.3,
        script: Optional[str] = None,
    ):
        if pyopenmv is None:
            raise RuntimeError("pyopenmv module is missing; install pyserial/Pillow or ensure pyopenmv.py is present.")
        if list_ports is None:
            raise RuntimeError("pyserial is missing; install it to talk to the OpenMV camera.")

        self.port = port or self._auto_port()
        self.baudrate = baudrate
        self.framesize = self._normalize_framesize(framesize)
        self.threshold = threshold
        self.scale = scale
        self.timeout = timeout
        self.script = script or DEFAULT_FACE_SCRIPT.format(
            framesize=self.framesize, threshold=self.threshold, scale=self.scale
        )
        self._last_reconnect = 0.0
        self._connect()

    def _normalize_framesize(self, framesize: str) -> str:
        allowed = {
            "QQVGA",
            "QVGA",
            "CIF",
            "VGA",
            "SVGA",
            "XGA",
            "SXGA",
            "UXGA",
        }
        fs = framesize.upper()
        if fs not in allowed:
            log.warning("Unsupported framesize '%s', defaulting to QVGA", framesize)
            fs = "QVGA"
        return fs

    def _auto_port(self) -> str:
        # Allow environment override for convenience.
        env_port = os.environ.get("OPENMV_PORT")
        if env_port:
            log.info("Using OPENMV_PORT=%s", env_port)
            return env_port

        if list_ports is None:
            raise RuntimeError("pyserial is missing; install it to auto-detect OpenMV.")

        ports = list(list_ports.comports())
        for port in ports:
            desc = (port.description or "") + (port.manufacturer or "")
            if "OpenMV" in desc:
                return port.device
        for port in ports:
            if port.device.startswith("/dev/ttyACM") or port.device.startswith("/dev/ttyUSB") or port.device.startswith("COM"):
                return port.device

        details = ", ".join(f"{p.device} ({p.description or ''})" for p in ports) or "none"
        raise RuntimeError(f"OpenMV device not found; available ports: {details}. Set cfg.openmv.port or OPENMV_PORT.")

    def _connect(self) -> None:
        log.info("Connecting to OpenMV on %s (baud=%s framesize=%s)", self.port, self.baudrate, self.framesize)
        pyopenmv.disconnect()
        pyopenmv.init(self.port, baudrate=self.baudrate, timeout=self.timeout)
        pyopenmv.stop_script()
        pyopenmv.enable_fb(True)
        pyopenmv.exec_script(self.script)
        time.sleep(0.25)
        pyopenmv.set_timeout(self.timeout)

    def _reconnect(self) -> None:
        now = time.time()
        if (now - self._last_reconnect) < 1.0:
            return
        self._last_reconnect = now
        try:
            self._connect()
        except Exception as exc:
            log.error("Failed to reconnect to OpenMV: %s", exc)

    def read(self) -> Optional[Tuple[bool, np.ndarray, List[Detection]]]:
        try:
            state = pyopenmv.read_state()
        except Exception as exc:
            log.warning("OpenMV read_state failed: %s", exc)
            self._reconnect()
            return None

        if not state or state[0] == 0 or state[2] is None:
            return None

        width, height, img, _, text, _, _ = state
        frame_rgb = np.asarray(img, dtype=np.uint8)
        frame_bgr = frame_rgb[:, :, ::-1]  # OpenMV uses RGB; OpenCV expects BGR.
        dets = self._parse_detections(text)
        return True, frame_bgr, dets

    def _parse_detections(self, text: Optional[str]) -> List[Detection]:
        if not text or not text.startswith("FACES:"):
            return []

        payload = text.split("FACES:", 1)[1]
        if not payload:
            return []

        dets: List[Detection] = []
        for chunk in payload.split("|"):
            if not chunk:
                continue
            try:
                x, y, w, h = map(int, chunk.split(","))
                dets.append(Detection((x, y, x + w, y + h), conf=1.0, cls=0))
            except Exception:
                continue
        return dets

    def release(self) -> None:
        try:
            pyopenmv.stop_script()
        except Exception:
            pass
        try:
            pyopenmv.disconnect()
        except Exception:
            pass
