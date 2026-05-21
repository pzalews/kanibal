from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class Status(str, Enum):
    TODO = "todo"
    WORKING = "working"
    DONE = "done"
    POSTPONED = "postponed"


MARKERS = {
    Status.TODO: " ",
    Status.WORKING: "/",
    Status.DONE: "x",
    Status.POSTPONED: "?",
}

MARKER_TO_STATUS = {v: k for k, v in MARKERS.items()}


@dataclass
class Task:
    status: Status
    title: str
    details: Optional[str] = None
    ticket: Optional[str] = None
    created: Optional[date] = None
    finished: Optional[date] = None
    line_index: Optional[int] = None
