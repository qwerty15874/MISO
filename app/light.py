import logging

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:
    GPIO = None  # type: ignore

log = logging.getLogger(__name__)


class LightController:
    def __init__(self, relay_pin: int = 23):
        self.relay_pin = relay_pin
        self.mock = GPIO is None
        if not self.mock:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay_pin, GPIO.OUT)
        log.info("Light controller initialized (mock=%s)", self.mock)

    def on(self) -> None:
        if self.mock:
            log.debug("Light ON (mock)")
            return
        GPIO.output(self.relay_pin, GPIO.HIGH)

    def off(self) -> None:
        if self.mock:
            log.debug("Light OFF (mock)")
            return
        GPIO.output(self.relay_pin, GPIO.LOW)
