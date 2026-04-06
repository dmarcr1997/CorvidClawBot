# Corvid Robotics: ClawBot

> A swarm of specialized AI agents that interpret natural language
> commands and dynamically rewrite robot behavior in real time —
> no manual coding required.

## Built With

- [OpenClaw](https://openclaw.ai) — Agent framework
- [Arduino Uno Q](https://arduino.cc) — STM32 + Linux SBC
- Telegram — Human interface

## What it is

ClawBot is an intelligent rover controlled by
natural language using Telegram. A swarm of agents on the Arduino
Uno Q linux chip interpret commands, generate new behavior,
validate it for safety, and live deploy it to the rover.
The rover wobbles while it thinks. Then it moves.

## How it works

Telegram
↓ natural language
Arduino Uno Q (OpenClaw + Agent Swarm)
↑ GET /capture ↓ GET /move
↑ frame stream ↓ motor commands
ESP32-S3 WROOM Rover (Camera + Motors)

## Repo Structure

```
clawbot/
  hardware/
    schematics/
  esp/
    CameraMotorServerBot/
      CameraWebServer.ino -> setup camera and webserver
      app_httpd.cpp -> webserver controls and motor logic
  skills/
  context/
    primitives.md
    base_rules.md
    behavior_template.md
  python/
    main.py
  sketch/
    sketch.ino
    sketch.yaml
  app.yaml
  blackboard.json
  README.md
```

## Blackboard

ClawBot uses a JSON blackboard as shared memory across the agent swarm.
Agents read and write to it to collaborate, wait on dependencies, and
handle rollbacks.

```json
{
  "robot_id": "rover_01",
  "health": {
    "hardware": "good",
    "alerts": [],
    "last_sensor_reading": {}
  },
  "current_code": {
    "base": { "filename": "base.ino", "hash": "abc123" },
    "behavior": { "filename": "behavior.py", "hash": "xyz789" }
  },
  "tasks": [],
  "override_mode": false
}
```

Tasks follow a dependency chain — a job won't execute until its
required dependencies resolve with the expected outcome. This is
how the validator blocks the flash agent from deploying bad code.

## Agents

| Agent     | Role                                                                                                   |
| --------- | ------------------------------------------------------------------------------------------------------ |
| Intent    | Parses natural language from Telegram, structures tasks on the blackboard, flags null/ambiguous params |
| Codegen   | Swarm of 3 sub-agents (write, review, test) that collaboratively generate behavior.py                  |
| Validator | Checks generated code against hardware constraints and base.ino rules before allowing flash            |
| Comms     | Only agent that talks to Telegram — sends status updates, asks clarifying questions, reports alerts    |
| Watchdog  | Monitors hardware health, sensor readings, raises alerts, can trigger emergency stop                   |

## Hardware

### ClawBot Rover

| Component                                 | Purpose                                                               |
| ----------------------------------------- | --------------------------------------------------------------------- |
| AI Thinker DIY Smart Car Chassis          | 4WD base platform                                                     |
| 4x Yellow DC Motors (2 per L298N channel) | Drive — left pair OUT1/OUT2, right pair OUT3/OUT4                     |
| L298N Motor Driver                        | Motor control — IN1→GPIO21, IN2→GPIO47, IN3→GPIO42, IN4→GPIO45        |
| Freenove ESP32-S3 WROOM                   | Onboard camera + WiFi web server — powered directly from L298N 5V out |

### ClawBot Brain

| Component                      | Purpose                                 |
| ------------------------------ | --------------------------------------- |
| Arduino Uno Q                  | Runs OpenClaw agent swarm on Linux side |
| Anker 10,000mAh 30W Power Bank | Powers Uno Q                            |

## Architecture

The system is split across two physical devices connected over WiFi.

**Rover (ESP32-S3 WROOM)** runs a lightweight HTTP web server exposing:

- `GET /capture` — returns a single JPEG frame from the onboard camera
- `GET /move?direction=forward|backward` — drive motors
- `GET /turn?direction=left|right` — turn motors
- `GET /stop` — stop all motors
- `GET /wobble` — wobble animation played during behavior updates

**Brain (Arduino Uno Q)** runs OpenClaw and the full agent swarm on its Linux side. It pulls camera frames from the rover, runs hierarchical Lucas-Kanade frame interpolation for a smooth vision feed, and sends motor commands back to the rover based on obstacle avoidance logic and user prompts from Telegram.

The comms agent sends Telegram updates including images when it detects something noteworthy — obstacles, targets acquired, behavior changes — so the user always has eyes on the rover without needing a separate app. All interaction happens entirely through Telegram.

## Demo Capabilities

- Indoor navigation with visual obstacle avoidance
- Follow a specified object
- Immediate stop on command
- Reverse a specified distance
- Turn around
- Learn and follow a face

## Where We're Going

ClawBot is the foundation of a larger vision for autonomous robot swarms.

| Milestone               | Description                                                                                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| All-weather 4x4 chassis | Ruggedized drive system for outdoor terrain                                                                                                      |
| Persistent skills       | Always-on capabilities that don't require behavior rewrites — object detection, visual odometry, sensor fusion, tracking, reinforcement learning |
| GPS + path following    | Autonomous waypoint navigation and route planning                                                                                                |
| Robot swarms            | Multi-robot coordination where ClawBot ecosystems work together                                                                                  |
| Commercial deployment   | Night patrol and security rovers for farms and private land                                                                                      |

The end goal: affordable, intelligent, self-coordinating robot swarms
that can be deployed and retasked in the field using nothing but
natural language.

## License

[MIT](./LICENSE)
