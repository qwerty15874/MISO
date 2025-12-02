"""
Entry point for the app-based face tracker.
- Defaults to the face model at Yolo_face_recognition_trained_50/yolo11n.pt.
- Uses app/ modules (camera, detector, controller, motor, light).
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is importable when running from test/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import AppConfig
from app.tracker import TrackerApp


def parse_args():
    p = argparse.ArgumentParser(description="Run face tracker (app modules).")
    p.add_argument("--camera-index", type=int, default=None, help="Camera index (override config)")
    p.add_argument("--width", type=int, default=None, help="Camera width (override config)")
    p.add_argument("--height", type=int, default=None, help="Camera height (override config)")
    p.add_argument("--fps", type=int, default=None, help="Camera FPS (override config)")
    p.add_argument("--model-path", type=str, default=None, help="Path to YOLO model (pt/onnx). Overrides config.")
    p.add_argument("--conf", type=float, default=None, help="Detection confidence threshold (override config).")
    p.add_argument("--timeout", type=float, default=None, help="Seconds until light off/home when no face (override config).")
    p.add_argument("--imgsz", type=int, default=None, help="Inference input size (override config).")
    return p.parse_args()


def build_config(args) -> AppConfig:
    cfg = AppConfig()
    if args.camera_index is not None:
        cfg.camera.device_index = args.camera_index
    if args.width is not None:
        cfg.camera.width = args.width
    if args.height is not None:
        cfg.camera.height = args.height
    if args.fps is not None:
        cfg.camera.fps = args.fps
    if args.conf is not None:
        cfg.detector.confidence = args.conf
    if args.timeout is not None:
        cfg.control.timeout_no_person_s = args.timeout
    if args.imgsz is not None:
        cfg.detector.imgsz = args.imgsz
    if args.model_path:
        cfg.detector.model_path = Path(args.model_path)
    return cfg


def main():
    args = parse_args()
    cfg = build_config(args)
    app = TrackerApp(cfg)
    app.run()


if __name__ == "__main__":
    main()
