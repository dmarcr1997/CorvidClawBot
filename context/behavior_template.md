# ClawBot Behavior Template

This is the required structure for all generated behavior.py files.
Codegen agents MUST follow this template. Do not deviate from this structure.

## Rules

- Always check blackboard at top of every loop iteration
- Always call `stop()` before switching directions
- Never remove the wobble/loading state handler
- Replace TARGET_LABEL with actual detection target
- Verify box keys match device output before deploying

## Detection Shape

```python
# detections = {label: [box, box, ...], ...}
# Each box is a dict — verify exact keys on device by printing raw detections
# Expected: x, y, width, height, confidence
# Frame dimensions: 1280x720
```

## Template

```python
import time
import json
from arduino.app_utils import App, Bridge
from arduino.app_bricks.video_objectdetection import VideoObjectDetection

# ── Constants ────────────────────────────────────────────────
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
OBSTACLE_LARGE_THRESHOLD = 0.3  # 30% of frame area
LOST_TARGET_FRAME_LIMIT = 10
DETECTION_CONFIDENCE = 0.5
TARGET_LABEL = "person"  # codegen replaces this

# ── State ────────────────────────────────────────────────────
last_known_position = None
lost_frames = 0
latest_detections = {}

# ── Detection Setup ──────────────────────────────────────────
detection_stream = VideoObjectDetection(confidence=DETECTION_CONFIDENCE, debounce_sec=0.0)

def on_detections(detections: dict):
    global latest_detections
    latest_detections = detections

detection_stream.on_detect_all(on_detections)

# ── Helpers ──────────────────────────────────────────────────
def read_blackboard() -> dict:
    with open("blackboard.json", "r") as f:
        return json.load(f)

def box_area(box) -> float:
    """Returns box area as fraction of total frame."""
    return (box["width"] * box["height"]) / (FRAME_WIDTH * FRAME_HEIGHT)

def box_center_x(box) -> float:
    """Returns horizontal center of box as fraction of frame width."""
    return (box["x"] + box["width"] / 2) / FRAME_WIDTH

def largest_box(boxes: list) -> dict:
    """Returns the largest bounding box by area."""
    return max(boxes, key=box_area)

# ── Main Loop ────────────────────────────────────────────────
def loop():
    global last_known_position, lost_frames

    # Always check blackboard first — implicit interrupt
    state = read_blackboard()
    if state.get("agent_loading"):
        Bridge.call("wobble")
        return

    obstacles = latest_detections.get("obstacle", [])
    targets = latest_detections.get(TARGET_LABEL, [])

    # ── Obstacle Avoidance ───────────────────────────────────
    if obstacles:
        box = largest_box(obstacles)
        area = box_area(box)
        center_x = box_center_x(box)
        is_large = area > OBSTACLE_LARGE_THRESHOLD
        is_center = 0.35 < center_x < 0.65
        is_left = center_x < 0.5
        is_right = center_x >= 0.5

        if is_large:
            if is_center:
                # Completely blocked — stop and alert
                Bridge.call("stop")
                # Write alert to blackboard for comms agent
                state["health"]["alerts"].append({
                    "type": "obstacle_blocked",
                    "message": "Rover completely blocked by obstacle",
                    "timestamp": time.time()
                })
                with open("blackboard.json", "w") as f:
                    json.dump(state, f)
            elif is_left:
                Bridge.call("stop")
                time.sleep(0.1)
                Bridge.call("turn", 60, False)  # turn right
            else:
                Bridge.call("stop")
                time.sleep(0.1)
                Bridge.call("turn", 60, True)   # turn left
        else:
            # Small obstacle — gentle correction
            if is_center:
                Bridge.call("stop")
                time.sleep(0.1)
                Bridge.call("turn", 30, is_right)
            elif is_right:
                Bridge.call("turn", 30, True)   # nudge left
            elif is_left:
                Bridge.call("turn", 30, False)  # nudge right

    # ── Target Following ─────────────────────────────────────
    if targets:
        box = largest_box(targets)
        center_x = box_center_x(box)
        last_known_position = center_x
        lost_frames = 0

        if center_x < 0.4:
            Bridge.call("stop")
            time.sleep(0.1)
            Bridge.call("turn", 40, True)    # turn left toward target
        elif center_x > 0.6:
            Bridge.call("stop")
            time.sleep(0.1)
            Bridge.call("turn", 40, False)   # turn right toward target
        else:
            Bridge.call("move", 50, True)    # target centered, move forward

    elif last_known_position is not None:
        # Follow last known position
        lost_frames += 1
        if lost_frames <= LOST_TARGET_FRAME_LIMIT:
            Bridge.call("turn", 30, last_known_position < 0.5)
        else:
            # Target lost — clear state and stop
            last_known_position = None
            lost_frames = 0
            Bridge.call("stop")

    time.sleep(0.05)  # ~20fps loop

App.run(user_loop=loop)
```

## Notes for Codegen

- Replace `TARGET_LABEL` with actual detection target e.g. `"face"`, `"person"`, `"cup"`
- Adjust `DETECTION_CONFIDENCE` per task — lower for harder targets
- Never remove the blackboard check at top of `loop()`
- Always `stop()` + `time.sleep(0.1)` before direction changes
- Obstacle avoidance runs before target following — priority order matters
- Write alerts to blackboard health.alerts for comms agent to pick up
- Keep all Bridge calls within primitives.md
- Verify box dictionary keys match device output before first deploy
