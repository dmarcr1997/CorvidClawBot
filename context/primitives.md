# ClawBot HTTP Primitives

These are the HTTP endpoints exposed by the ESP32-S3 WROOM rover web server.
Codegen agents MUST only use these endpoints in behavior.py.

## Rover Base URL

```python
ROVER_URL = "http://192.168.1.99"
```

## Movement Endpoints

| Endpoint                      | Params                       | Description                                      |
| ----------------------------- | ---------------------------- | ------------------------------------------------ |
| `GET /move?direction=forward` | direction: forward\|backward | Drive rover forward or backward                  |
| `GET /turn?direction=left`    | direction: left\|right       | Turn rover left or right                         |
| `GET /stop`                   | none                         | Immediately stop all motors                      |
| `GET /wobble`                 | none                         | Wobble animation — plays during behavior updates |

## Vision Endpoint

| Endpoint       | Returns    | Description                      |
| -------------- | ---------- | -------------------------------- |
| `GET /capture` | JPEG bytes | Single frame from onboard camera |

## Usage in behavior.py

```python
import requests

ROVER_URL = "http://192.168.1.99"

# Movement
requests.get(f"{ROVER_URL}/move?direction=forward", timeout=1)
requests.get(f"{ROVER_URL}/move?direction=backward", timeout=1)
requests.get(f"{ROVER_URL}/turn?direction=left", timeout=1)
requests.get(f"{ROVER_URL}/turn?direction=right", timeout=1)
requests.get(f"{ROVER_URL}/stop", timeout=1)
requests.get(f"{ROVER_URL}/wobble", timeout=1)

# Vision
response = requests.get(f"{ROVER_URL}/capture", timeout=2)
img_array = np.frombuffer(response.content, dtype=np.uint8)
frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
```

## Safety Rules

- Always call `/stop` before switching directions
- Always wrap HTTP calls in try/except — rover may be briefly unavailable
- Use timeout=1 for movement calls, timeout=2 for capture calls
- Recommended movement call spacing: 0.1s minimum between calls

## Hardware

| Component        | Detail                                            |
| ---------------- | ------------------------------------------------- |
| Board            | Freenove ESP32-S3 WROOM                           |
| Motor Driver     | L298N — ENA/ENB hardwired HIGH, no speed control  |
| Motor Pins       | IN1→GPIO21, IN2→GPIO47, IN3→GPIO42, IN4→GPIO45    |
| Camera           | Onboard ESP32-S3 camera, captures at 320x240 JPEG |
| Frame dimensions | 320x240 (raw from rover)                          |
