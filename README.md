# Raspberry Pi Face Tracker (TB6600)

OpenMV handles camera + face detection; host PC/Raspberry Pi receives frames/detections over USB and drives the TB6600 stepper + light.

## Requirements
- Raspberry Pi OS 64-bit recommended
- Python 3.10+
- OpenMV Cam (H7/H7 Plus, etc.) over USB (used for both capture and face detection)
- TB6600 + stepper (STM-4224 in my setup), relay for the light
- `pip install -r requirements.txt`
  - Includes `pyserial` + `Pillow` for OpenMV host streaming.

## Layout
- `app/config.py` - camera/control/light/OpenMV settings
- `app/camera.py` - OpenCV capture wrapper (kept for reference)
- `app/detector.py` - face_recognition-based face detector (kept for reference; not used when OpenMV is enabled)
- `app/openmv_client.py` - OpenMV USB client; streams frames + Haar face boxes from the camera
- `app/motor_driver.py` - TB6600 PUL/DIR/ENA driver (mock-friendly)
- `app/controller.py` - PD control converting pixels -> step commands
- `app/light.py` - relay on/off
- `app/tracker.py` - main loop tying everything together

## Run
```bash
pip install -r requirements.txt
# OpenMV backend (camera + Haar face detection runs on the OpenMV cam)
# auto-detects the USB/serial port; override with --openmv-port if needed
python -m app.tracker
# or override on the CLI, e.g.:
python test/test.py --openmv --openmv-port /dev/ttyACM0 --openmv-framesize QVGA --openmv-threshold 0.7 --openmv-scale 1.35
```

## Flow
1. OpenMV captures a frame and runs Haar cascade face detection.
2. Host receives the frame + bounding boxes; picks the largest face.
3. Compute pixel error from image center -> PD -> TB6600 steps.
4. Turn light on while a face is seen; after `timeout_no_person_s` turn it off and home the motor.

## Tuning tips
- Match `camera_hfov_deg` to your lens
- Adjust `kp/kd` and `deadband_px` for smooth tracking
- `steps_per_rev`, `microstep`, `gear_ratio` should match your motor/driver setup
- `max_speed_sps` keeps motion safe; start low and increase with testing
- For OpenMV: `openmv.framesize` must be a supported sensor size (e.g., QVGA/VGA); tweak `openmv.threshold`/`openmv.scale` to balance sensitivity vs noise.
