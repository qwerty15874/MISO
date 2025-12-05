"""
Entry point for the OpenMV-based face tracker (controller, motor, light on the host).
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
    p.add_argument("--timeout", type=float, default=None, help="Seconds until light off/home when no face (override config).")
    p.add_argument("--openmv", action="store_true", help="Use OpenMV for camera + face detection (default).")
    p.add_argument("--openmv-port", type=str, default=None, help="Serial port for OpenMV (auto-detect if omitted).")
    p.add_argument("--openmv-framesize", type=str, default=None, help="OpenMV framesize (e.g., QVGA, VGA).")
    p.add_argument("--openmv-threshold", type=float, default=None, help="Haar cascade threshold on OpenMV.")
    p.add_argument("--openmv-scale", type=float, default=None, help="Haar cascade scale on OpenMV.")
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
    if args.timeout is not None:
        cfg.control.timeout_no_person_s = args.timeout
    if args.openmv:
        cfg.openmv.enabled = True
    if args.openmv_port is not None:
        cfg.openmv.port = args.openmv_port
    if args.openmv_framesize is not None:
        cfg.openmv.framesize = args.openmv_framesize
    if args.openmv_threshold is not None:
        cfg.openmv.threshold = args.openmv_threshold
    if args.openmv_scale is not None:
        cfg.openmv.scale = args.openmv_scale
    return cfg


def main():
    args = parse_args()
    cfg = build_config(args)
    app = TrackerApp(cfg)
    app.run()


if __name__ == "__main__":
    main()
