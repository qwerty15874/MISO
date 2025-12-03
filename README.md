# Raspberry Pi Face Tracker (TB6600)

Camera feed -> `face_recognition` detector -> TB6600 stepper + relay to keep a light pointed at the visible face.

## Requirements
- Raspberry Pi OS 64-bit recommended
- Python 3.10+
- UVC or Pi camera
- TB6600 + stepper (STM-4224 in my setup), relay for the light
- `pip install -r requirements.txt`
  - `face-recognition` uses `dlib`; install build deps first on Pi (`cmake`, `boost`, `openblas`).

## Layout
- `app/config.py` - camera/control/light/detector settings
- `app/camera.py` - OpenCV capture wrapper
- `app/detector.py` - face_recognition-based face detector
- `app/motor_driver.py` - TB6600 PUL/DIR/ENA driver (mock-friendly)
- `app/controller.py` - PD control converting pixels -> step commands
- `app/light.py` - relay on/off
- `app/tracker.py` - main loop tying everything together

## Run
```bash
pip install -r requirements.txt
# defaults tuned for Pi 4B: 640x480@12fps, hog model, resize_width=320, upsample=0
# tweak config.py for camera_hfov_deg, kp/kd, model (hog/cnn), resize_width, etc.
python -m app.tracker
# or override on the CLI, e.g.:
# python test/test.py --model hog --upsample 0 --det-resize-width 320 --fps 12 --width 640 --height 480
```

## Flow
1. Capture frame
2. `face_recognition.face_locations` finds faces; pick the largest bounding box
3. Compute pixel error from image center -> PD -> TB6600 steps
4. Turn light on while a face is seen; after `timeout_no_person_s` turn it off and home the motor

## Tuning tips
- Match `camera_hfov_deg` to your lens
- Adjust `kp/kd` and `deadband_px` for smooth tracking
- `steps_per_rev`, `microstep`, `gear_ratio` should match your motor/driver setup
- `max_speed_sps` keeps motion safe; start low and increase with testing
- Keep `upsample` at 0 and `resize_width` small (e.g., 320) for best speed on Pi 4B; increase only if detection misses faces
