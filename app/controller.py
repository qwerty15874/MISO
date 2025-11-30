import logging
from dataclasses import dataclass

from .config import ControlConfig
from .motor_driver import MotorDriver

log = logging.getLogger(__name__)


@dataclass
class ControlState:
    current_steps: int = 0
    last_error_px: float = 0.0


class MotorController:
    def __init__(self, cfg: ControlConfig, driver: MotorDriver):
        self.cfg = cfg
        self.driver = driver
        self.state = ControlState()
        self.driver.enable()

    def px_to_steps(self, error_px: float, frame_width: int) -> int:
        deg_per_px = self.cfg.camera_hfov_deg / frame_width
        error_deg = error_px * deg_per_px
        steps_per_deg = (
            self.cfg.steps_per_rev * self.cfg.microstep * self.cfg.gear_ratio
        ) / 360.0
        return int(error_deg * steps_per_deg)

    def compute_step_command(self, error_px: float, frame_width: int, dt: float) -> int:
        derivative = (error_px - self.state.last_error_px) / dt if dt > 0 else 0.0
        control_px = self.cfg.kp * error_px + self.cfg.kd * derivative
        steps = self.px_to_steps(control_px, frame_width)
        if abs(error_px) < self.cfg.deadband_px:
            steps = 0
        self.state.last_error_px = error_px
        return steps

    def move(self, steps: int) -> None:
        if steps == 0:
            return
        step_delay_s = max(1.0 / self.cfg.max_speed_sps, 0.0002)
        self.driver.step(steps, step_delay_s)
        self.state.current_steps += steps

    def home(self) -> None:
        self.driver.home(self.cfg.home_position_steps)
        self.state.current_steps = 0

    def shutdown(self) -> None:
        self.driver.disable()
