from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CameraConfig:
    device_index: int = 0
    width: int = 1920  # 720p width
    height: int = 1080  # 720p height
    fps: int = 15


@dataclass
class DetectorConfig:
    # Default to face-trained weights under Yolo_face_recognition_trained_50
    model_path: Optional[Path] = Path("Yolo_face_recognition_trained_50/yolo11n.pt")
    confidence: float = 0.35
    person_class_id: int = 0  # face class id in the custom model
    half_precision: bool = True
    max_det: int = 5
    imgsz: int = 480  # reduce input size for faster inference


@dataclass
class ControlConfig:
    kp: float = 0.4
    kd: float = 0.05
    deadband_px: int = 10
    camera_hfov_deg: float = 50.0  # adjust to your lens HFOV
    steps_per_rev: int = 200
    microstep: int = 8  # TB6600 DIP setting
    gear_ratio: float = 1.0
    max_speed_sps: int = 2000  # steps per second
    accel_sps2: int = 4000  # steps per second^2 (not yet used)
    home_position_steps: int = 0
    timeout_no_person_s: float = 4.0


@dataclass
class LightConfig:
    relay_pin: int = 23


@dataclass
class AppConfig:
    camera: CameraConfig = CameraConfig()
    detector: DetectorConfig = DetectorConfig()
    control: ControlConfig = ControlConfig()
    light: LightConfig = LightConfig()
