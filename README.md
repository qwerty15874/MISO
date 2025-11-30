# Raspberry Pi YOLO11n Person Tracker (TB6600)

카메라 → YOLO11n → 사람 감지 → TB6600 스텝모터로 조명 방향 추적 → 릴레이로 조명 온/오프 하는 최소 구현 스켈레톤입니다. Firebase/버튼/부저는 제외했습니다.

## 요구사항
- Raspberry Pi OS 64-bit 추천
- Python 3.10+
- 카메라(UVC 또는 Pi 카메라)
- TB6600 + 스텝모터(STM-4224 등), 릴레이 모듈
- 패키지: `pip install -r requirements.txt`
  - `ultralytics`가 없으면 감지기는 빈 결과만 반환합니다. yolo11n.pt(또는 ONNX) 파일을 로컬에 두고 경로를 설정하세요.

## 구성
- `app/config.py` — 카메라/검출/제어/릴레이 파라미터
- `app/camera.py` — OpenCV 캡처
- `app/detector.py` — YOLO11n 감지기(ultralytics)
- `app/motor_driver.py` — TB6600 PUL/DIR/ENA 제어(mock 지원)
- `app/controller.py` — 픽셀 오차→스텝 변환, P/PD 제어
- `app/light.py` — 릴레이 제어
- `app/tracker.py` — 메인 루프

## 실행
```bash
pip install -r requirements.txt
# config.py에서 model_path, 핀 번호, HFOV, 마이크로스텝 등 조정
python -m app.tracker
```

## 동작 흐름
1. 카메라 프레임 캡처
2. YOLO11n으로 person 감지 → 가장 큰 박스 선택
3. 이미지 중심 대비 X축 오차→P/PD로 스텝 수 계산→TB6600에 펄스
4. 감지 시 릴레이 ON, 미검출 `timeout_no_person_s` 경과 시 릴레이 OFF + 홈 복귀

## 튜닝 팁
- `camera_hfov_deg`를 카메라 렌즈 HFOV에 맞춰 수정
- `kp/kd`와 `deadband_px`로 떨림을 줄이기
- `steps_per_rev`, `microstep`, `gear_ratio`를 실제 TB6600 DIP/기어비에 맞게 설정
- `max_speed_sps`를 과도하게 높이면 모터 실동작 속도를 초과할 수 있으니 점진적으로 올려 테스트
