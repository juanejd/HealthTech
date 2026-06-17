from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE: Path = Path(__file__).parent.parent / "logs" / "events.log"


def log_event(
    event_type: str,
    status: str,
    extraction_detected: bool,
    day: str,
    compartment_index: int,
) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": event_type,
        "status": status,
        "extraction_detected": extraction_detected,
        "day": day,
        "compartment_index": compartment_index,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def read_events() -> list:
    if not LOG_FILE.exists():
        return []
    events = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return list(reversed(events))
