import logging
import signal
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

import cv2
import numpy as np

from .camera import Camera
from .config import AppConfig
from .controller import MotorController
from .detector import YOLODetector
from .light import LightController
from .motor_driver import TB6600Driver

log = logging.getLogger(__name__)


class TrackerApp:
    """Minimal camera → YOLO → motor + light tracking loop."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.camera = Camera(
            device_index=cfg.camera.device_index,
            width=cfg.camera.width,
            height=cfg.camera.height,
            fps=cfg.camera.fps,
        )
        self.detector = YOLODetector(
            model_path=str(cfg.detector.model_path) if cfg.detector.model_path else None,
            person_class_id=cfg.detector.person_class_id,
            conf=cfg.detector.confidence,
            max_det=cfg.detector.max_det,
            half=cfg.detector.half_precision,
        )
        self.motor_driver = TB6600Driver()
        self.controller = MotorController(cfg.control, self.motor_driver)
        self.light = LightController(cfg.light.relay_pin)
        self._last_steps = 0
        self._light_on = False
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._pending: Optional[Future] = None
        self._latest_dets = []
        self._running = True
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

    def _stop(self, *args) -> None:
        log.info("Stopping...")
        self._running = False

    def _pick_person(self, dets):
        if not dets:
            return None
        dets = [d for d in dets if d.cls == self.cfg.detector.person_class_id]
        if not dets:
            return None
        return max(dets, key=lambda d: (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]))

    def run(self) -> None:
        last_seen = time.time()
        self.light.off()

        while self._running:
            loop_start = time.time()
            frame_data = self.camera.read()
            if frame_data is None:
                time.sleep(0.05)
                continue

            _, frame = frame_data
            # Async detection: fetch completed results, then submit the latest frame if idle.
            self._collect_future()
            self._submit_future(frame)
            dets = self._latest_dets
            person = self._pick_person(dets)
            frame_center_x = frame.shape[1] / 2
            frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
            error_px = None
            steps = 0

            if person:
                now = time.time()
                dt = max(now - loop_start, 1e-3)
                last_seen = now
                cx, cy = person.center
                error_px = cx - frame_center_x
                steps = self.controller.compute_step_command(error_px, frame.shape[1], dt=dt)
                self.controller.move(steps)
                self.light.on()
                self._light_on = True
                self._last_steps = steps
                log.info(
                    "Person conf=%.2f bbox=%s error_px=%.1f steps=%d",
                    person.conf,
                    tuple(round(v, 1) for v in person.bbox),
                    error_px,
                    steps,
                )
                # Draw overlay
                x1, y1, x2, y2 = map(int, person.bbox)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (int(cx), int(cy)), 3, (0, 255, 0), -1)
                cv2.circle(frame, frame_center, 3, (0, 0, 255), -1)
                cv2.putText(
                    frame,
                    f"err={error_px:.1f}px steps={steps}",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )
            else:
                if time.time() - last_seen > self.cfg.control.timeout_no_person_s:
                    self.light.off()
                    self._light_on = False
                self.controller.home()

            self._show(frame, status=self._status_text(person, error_px, steps, frame_center))

            elapsed = time.time() - loop_start
            # To keep UI snappy, skip sleeping unless loop is faster than target FPS.
            sleep_time = max(0, (1 / self.cfg.camera.fps) - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.controller.shutdown()
        self.camera.release()
        self._executor.shutdown(wait=False)

    def _status_text(self, person, error_px, steps, frame_center):
        if person:
            cx, cy = person.center
            face_txt = f"Face ({int(cx)},{int(cy)}) conf={person.conf:.2f}"
            err_txt = f"ErrorX={error_px:.1f}px Steps={steps}"
        else:
            face_txt = "Face: none"
            err_txt = "ErrorX: n/a Steps: 0"
        return [
            "Tracker status",
            face_txt,
            err_txt,
            f"Center: ({frame_center[0]},{frame_center[1]})",
            f"Motor last cmd: {self._last_steps} steps | Pos: {self.controller.state.current_steps}",
            f"Light: {'ON' if self._light_on else 'OFF'}",
            "Press 'q' to quit",
        ]

    def _show(self, frame, status):
        try:
            cv2.imshow("camera", frame)
            canvas = np.zeros((180, 420, 3), dtype=np.uint8)
            cv2.rectangle(canvas, (0, 0), (canvas.shape[1] - 1, canvas.shape[0] - 1), (200, 200, 200), 1)
            y = 25
            for line in status:
                cv2.putText(canvas, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                y += 28
            cv2.imshow("status", canvas)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self._stop()
        except cv2.error:
            pass

    def _submit_future(self, frame):
        if self._pending is None:
            # Copy to avoid race with UI drawing
            self._pending = self._executor.submit(self.detector, frame.copy())

    def _collect_future(self):
        if self._pending is not None and self._pending.done():
            try:
                self._latest_dets = self._pending.result()
            except Exception as exc:
                log.warning("Detector future failed: %s", exc)
                self._latest_dets = []
            finally:
                self._pending = None


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = AppConfig()
    app = TrackerApp(cfg)
    app.run()


if __name__ == "__main__":
    main()
