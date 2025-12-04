from dataclasses import dataclass, field


@dataclass
class CameraConfig:
    device_index: int = 0
    width: int = 560  # lower res for faster real-time detection
    height: int = 360
    fps: int = 24  # balance latency vs CPU load on Pi 4B


@dataclass
class DetectorConfig:
    model: str = "hog"  # "hog" (CPU) or "cnn" (GPU/NEON)
    upsample: int = 1   # no upsample for speed; better latency for real-time
    resize_width: int = 240  # more aggressive downscale for throughput
    use_fallback: bool = False  # disable slow second pass for steady FPS
    fallback_model: str = "hog"
    fallback_upsample: int = 1
    fallback_resize_width: int = 480  # optional if fallback is manually enabled


@dataclass
class ControlConfig:
    kp: float = 0.6          # faster response for rapid motion
    kd: float = 0.08         # a touch more damping to avoid overshoot
    deadband_px: int = 6     # react sooner to movement
    camera_hfov_deg: float = 50.0  # adjust to your lens HFOV
    steps_per_rev: int = 200
    microstep: int = 8  # TB6600 DIP setting
    gear_ratio: float = 1.0
    max_speed_sps: int = 2800  # allow faster slews; reduce if motor skips
    accel_sps2: int = 4000  # steps per second^2 (not yet used)
    home_position_steps: int = 0
    timeout_no_person_s: float = 4.0


@dataclass
class LightConfig:
    relay_pin: int = 23


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    light: LightConfig = field(default_factory=LightConfig)
