# ClawBot Bridge Primitives

These are the RPC functions exposed by the STM32 side via Arduino_RouterBridge.
Codegen agents MUST only use these functions in behavior.py.

## Movement

| Function               | Params                      | Description                                      |
| ---------------------- | --------------------------- | ------------------------------------------------ |
| `move(speed, forward)` | speed: 0-100, forward: bool | Move rover forward or backward                   |
| `turn(speed, left)`    | speed: 0-100, left: bool    | Turn rover left or right                         |
| `stop()`               | none                        | Immediately stop all motors                      |
| `wobble()`             | none                        | Wobble animation — plays during behavior updates |

## Sensors

| Function               | Params | Description                                       |
| ---------------------- | ------ | ------------------------------------------------- |
| `get_sensor_reading()` | none   | Returns current sensor data (stub — expand later) |

## Speed

- Range: 0-100 (percentage)
- Internally mapped to 0-200 PWM to protect motors
- Recommended range for normal operation: 30-70

## Pin Mapping (update when DRV8833 arrives)

| Pin | Assignment |
| --- | ---------- |
| 5   | AIN1       |
| 6   | AIN2       |
| 9   | BIN1       |
| 10  | BIN2       |
