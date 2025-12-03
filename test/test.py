"""
Entry point for the app-based face tracker.
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
    p.add_argument(
        "--model",
        type=str,
        default=None,
        choices=["hog", "cnn"],
        help="face_recognition model backend (hog=CPU, cnn=GPU/NEON). Overrides config.",
    )
    p.add_argument("--upsample", type=int, default=None, help="Number of upsampling passes for detection.")
    p.add_argument("--det-resize-width", type=int, default=None, help="Resize frame width before detection for speed.")
    p.add_argument("--timeout", type=float, default=None, help="Seconds until light off/home when no face (override config).")
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
    if args.model is not None:
        cfg.detector.model = args.model
    if args.upsample is not None:
        cfg.detector.upsample = args.upsample
    if args.det_resize_width is not None:
        cfg.detector.resize_width = args.det_resize_width
    if args.timeout is not None:
        cfg.control.timeout_no_person_s = args.timeout
    return cfg


def main():
    args = parse_args()
    cfg = build_config(args)
    app = TrackerApp(cfg)
    app.run()


if __name__ == "__main__":
    main()
