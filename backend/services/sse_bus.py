from __future__ import annotations

import json
import queue
from typing import Dict, Any, List

_subscribers: List["queue.Queue[str]"] = []


def subscribe() -> "queue.Queue[str]":
    q: "queue.Queue[str]" = queue.Queue(maxsize=100)
    _subscribers.append(q)
    return q


def unsubscribe(q: "queue.Queue[str]"):
    try:
        _subscribers.remove(q)
    except ValueError:
        pass


def publish_event(evt: Dict[str, Any]):
    line = f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(line)
        except Exception:
            dead.append(q)
    for q in dead:
        unsubscribe(q)
