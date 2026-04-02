# ClawBot Base Rules

These rules are enforced by the Validator agent before any behavior.py
is deployed. Violations will result in the task being rejected and
rolled back.

## Hard Rules — Never Violate

- Never write to hardware registers directly
- No AVR-specific code of any kind
- Never generate or modify .ino files (base layer is locked)
- Never define your own motor control logic — use Bridge RPCs only
- Never call undefined Bridge functions — only use what is in primitives.md

## Motor Safety

- Always call `stop()` before switching directions to prevent current spikes
- Never switch from full forward to full backward instantly
- Recommended pattern for direction change:

```python
  Bridge.call("stop")
  time.sleep(0.1)
  Bridge.call("move", speed, False)
```

- Keep speed in normal range 30-70 for sustained movement
- Only exceed 70 for short bursts

## Vision

Codegen agents may use VideoObjectDetection for behavior logic.
Template based detection is allowed on top of the video detection brick.

```python
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)
detection_stream.on_detect("face", callback)
detection_stream.on_detect_all(callback)
```

Available detection targets include but are not limited to:

- `face`
- `person`
- Any object label supported by the VideoObjectDetection brick

## Advanced Mode — .ino Editing

Users can opt into advanced mode to allow base.ino editing and rule
bypassing. This requires the following workflow without exception:

1. **Plan** — codegen drafts proposed .ino changes
2. **Showcase** — comms agent presents full plan to user via Telegram
3. **Permission** — user must explicitly confirm even after enabling advanced mode
4. **Second validation** — validator runs additional checks on generated .ino
5. **Build/Flash** — only after all above steps complete successfully

Advanced mode is tracked in the blackboard:

```json
{
  "override_mode": true
}
```
