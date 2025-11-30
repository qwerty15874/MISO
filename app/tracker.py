import logging
import signal
import time
from typing import Optional

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
            dets = self.detector(frame)
            person = self._pick_person(dets)
            frame_center_x = frame.shape[1] / 2

            if person:
                now = time.time()
                dt = max(now - loop_start, 1e-3)
                last_seen = now
                cx, _ = person.center
                error_px = cx - frame_center_x
                steps = self.controller.compute_step_command(error_px, frame.shape[1], dt=dt)
                self.controller.move(steps)
                self.light.on()
                log.info(
                    "Person conf=%.2f bbox=%s error_px=%.1f steps=%d",
                    person.conf,
                    tuple(round(v, 1) for v in person.bbox),
                    error_px,
                    steps,
                )
            else:
                if time.time() - last_seen > self.cfg.control.timeout_no_person_s:
                    self.light.off()
                    self.controller.home()

            elapsed = time.time() - loop_start
            sleep_time = max(0, (1 / self.cfg.camera.fps) - elapsed)
            time.sleep(sleep_time)

        self.controller.shutdown()
        self.camera.release()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = AppConfig()
    app = TrackerApp(cfg)
    app.run()


if __name__ == "__main__":
    main()
