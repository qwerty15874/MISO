import logging
import time
from typing import Protocol

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:
    GPIO = None  # type: ignore

log = logging.getLogger(__name__)


class MotorDriver(Protocol):
    def enable(self) -> None: ...
    def disable(self) -> None: ...
    def step(self, steps: int, step_delay_s: float) -> None: ...
    def home(self, home_steps: int = 0) -> None: ...


class TB6600Driver:
    """PUL/DIR/ENA stepper driver. Acts as mock when RPi.GPIO is absent."""

    def __init__(self, pul_pin: int = 17, dir_pin: int = 27, ena_pin: int = 22):
        self.pul_pin = pul_pin
        self.dir_pin = dir_pin
        self.ena_pin = ena_pin
        self.mock = GPIO is None
        if not self.mock:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pul_pin, GPIO.OUT)
            GPIO.setup(self.dir_pin, GPIO.OUT)
            GPIO.setup(self.ena_pin, GPIO.OUT)
        log.info("TB6600 driver initialized (mock=%s)", self.mock)

    def enable(self) -> None:
        if self.mock:
            log.debug("Enable (mock)")
            return
        GPIO.output(self.ena_pin, GPIO.HIGH)

    def disable(self) -> None:
        if self.mock:
            log.debug("Disable (mock)")
            return
        GPIO.output(self.ena_pin, GPIO.LOW)

    def step(self, steps: int, step_delay_s: float) -> None:
        if steps == 0:
            return
        if self.mock:
            log.debug("Step (mock): steps=%s delay=%.6f", steps, step_delay_s)
            time.sleep(abs(steps) * step_delay_s)
            return

        direction = GPIO.HIGH if steps > 0 else GPIO.LOW
        GPIO.output(self.dir_pin, direction)
        for _ in range(abs(steps)):
            GPIO.output(self.pul_pin, GPIO.HIGH)
            time.sleep(step_delay_s / 2)
            GPIO.output(self.pul_pin, GPIO.LOW)
            time.sleep(step_delay_s / 2)

    def home(self, home_steps: int = 0) -> None:
        self.step(-home_steps, step_delay_s=0.002)
