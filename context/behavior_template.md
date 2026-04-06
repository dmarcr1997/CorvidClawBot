# ClawBot Behavior Template

This is the required structure for all generated behavior.py files.
Codegen agents MUST follow this template. Do not deviate from this structure.

## Rules

- Always check blackboard at top of every loop iteration
- Always call /stop before switching directions
- Never remove the wobble/loading state handler
- Replace TARGET_LABEL with actual detection target
- Always wrap HTTP calls in try/except
- Always use the interpolated_stream for vision — never call /capture directly

## Detection Shape

```python
# frame = numpy BGR image from interpolated_stream
# Run YoloX or cv2 detection on frame directly
# Frame dimensions after upscale: 640x480
```

## Template

```python
import time
import json
import requests
import cv2
import numpy as np
import threading
import queue

# ── Constants ────────────────────────────────────────────────
ROVER_URL = "http://192.168.1.99"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
OBSTACLE_LARGE_THRESHOLD = 0.3
LOST_TARGET_FRAME_LIMIT = 10
TARGET_LABEL = "person"  # codegen replaces this

# ── State ────────────────────────────────────────────────────
last_known_position = None
lost_frames = 0

# ── Helpers ──────────────────────────────────────────────────
def read_blackboard() -> dict:
    with open("blackboard.json", "r") as f:
        return json.load(f)

def write_blackboard(state: dict):
    with open("blackboard.json", "w") as f:
        json.dump(state, f)

def stop():
    try:
        requests.get(f"{ROVER_URL}/stop", timeout=1)
    except Exception:
        pass

def move(direction: str):
    try:
        requests.get(f"{ROVER_URL}/move?direction={direction}", timeout=1)
    except Exception:
        pass

def turn(direction: str):
    try:
        requests.get(f"{ROVER_URL}/turn?direction={direction}", timeout=1)
    except Exception:
        pass

def box_area(box) -> float:
    return (box["width"] * box["height"]) / (FRAME_WIDTH * FRAME_HEIGHT)

def box_center_x(box) -> float:
    return (box["x"] + box["width"] / 2) / FRAME_WIDTH

def largest_box(boxes: list) -> dict:
    return max(boxes, key=box_area)

def get_detections(frame) -> dict:
    """Run detection on frame — codegen fills this in per task."""
    # Example: return {"person": [{"x": 100, "y": 100, "width": 50, "height": 80}]}
    return {}

# ── Main Loop ────────────────────────────────────────────────
def loop(frame):
    global last_known_position, lost_frames

    # Always check blackboard first — implicit interrupt
    state = read_blackboard()
    if state.get("agent_loading"):
        try:
            requests.get(f"{ROVER_URL}/wobble", timeout=1)
        except Exception:
            pass
        return

    detections = get_detections(frame)
    obstacles = detections.get("obstacle", [])
    targets = detections.get(TARGET_LABEL, [])

    # ── Obstacle Avoidance ───────────────────────────────────
    if obstacles:
        box = largest_box(obstacles)
        area = box_area(box)
        center_x = box_center_x(box)
        is_large = area > OBSTACLE_LARGE_THRESHOLD
        is_center = 0.35 < center_x < 0.65
        is_left = center_x < 0.5

        if is_large:
            if is_center:
                stop()
                state["health"]["alerts"].append({
                    "type": "obstacle_blocked",
                    "message": "Rover completely blocked by obstacle",
                    "timestamp": time.time(),
                    "acknowledged": False
                })
                write_blackboard(state)
            elif is_left:
                stop()
                time.sleep(0.1)
                turn("right")
            else:
                stop()
                time.sleep(0.1)
                turn("left")
        else:
            if is_center:
                stop()
                time.sleep(0.1)
                turn("right" if center_x >= 0.5 else "left")
            elif center_x >= 0.5:
                turn("left")
            else:
                turn("right")

    # ── Target Following ─────────────────────────────────────
    if targets:
        box = largest_box(targets)
        center_x = box_center_x(box)
        last_known_position = center_x
        lost_frames = 0

        if center_x < 0.4:
            stop()
            time.sleep(0.1)
            turn("left")
        elif center_x > 0.6:
            stop()
            time.sleep(0.1)
            turn("right")
        else:
            move("forward")

    elif last_known_position is not None:
        lost_frames += 1
        if lost_frames <= LOST_TARGET_FRAME_LIMIT:
            turn("left" if last_known_position < 0.5 else "right")
        else:
            last_known_position = None
            lost_frames = 0
            stop()

# ── Stream + Run ─────────────────────────────────────────────
if __name__ == "__main__":
    from stream import interpolated_stream
    for frame in interpolated_stream(capture_fps=10, interp_steps=5):
        loop(frame)
```

## Notes for Codegen

- Replace `TARGET_LABEL` with actual detection target
- Fill in `get_detections()` with appropriate detection logic per task
- Never call `/capture` directly — always use `interpolated_stream`
- Never remove the blackboard check at top of `loop()`
- Always `stop()` + `time.sleep(0.1)` before direction changes
- Obstacle avoidance runs before target following — priority order matters
- Write alerts to `blackboard.health.alerts` for comms to pick up
- Verify detection box keys match device output on first run
- Frame dimensions after upscale: 640x480
- write behavior.py to main.py or up
