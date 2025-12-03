from dataclasses import dataclass


@dataclass
class CameraConfig:
    device_index: int = 0
    width: int = 640  # lower for Pi 4B
    height: int = 480
    fps: int = 12


@dataclass
class DetectorConfig:
    model: str = "hog"  # "hog" (CPU) or "cnn" (GPU/NEON)
    upsample: int = 0   # 0 for speed on Pi
    resize_width: int = 320  # downscale before detection for speed


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
