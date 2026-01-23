# telemetry.py
import time, json, logging
logging.basicConfig(filename="agent.log", level=logging.INFO)

def log_event(kind: str, **kwargs):
    logging.info(json.dumps({"ts": time.time(), "kind": kind, **kwargs}))