# Default behavior — rover idle, waiting for first command
import time
import json
import requests

ROVER_URL = "http://192.168.1.99"

def read_blackboard() -> dict:
    with open("blackboard.json", "r") as f:
        return json.load(f)

from stream import interpolated_stream

for frame in interpolated_stream(capture_fps=20, interp_steps=5):
    state = read_blackboard()
    if state.get("agent_loading"):
        try:
            requests.get(f"{ROVER_URL}/wobble", timeout=1)
        except Exception:
            pass
    # idle — waiting for codegen to replace this file
    time.sleep(0.05)