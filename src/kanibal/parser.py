from __future__ import annotations

import re
from datetime import date
from typing import Optional, Tuple

from kanibal.models import MARKER_TO_STATUS, MARKERS, Task

LINE_RE = re.compile(r"^- \[(?P<marker>[ /x?])\] (?P<body>.+)$")
DATE_TAG_RE = re.compile(r"\s+@(created|finished):(\d{4}-\d{2}-\d{2})\b")
TICKET_TRAILING_RE = re.compile(r"\s+#([A-Z][A-Z0-9-]*)\s*$")
DETAILS_TRAILING_RE = re.compile(r"\s+\(([^()]*)\)\s*$")
TICKET_TOKEN = r"[A-Z][A-Z0-9-]*"


def _extract_dates(body: str) -> Tuple[str, Optional[date], Optional[date]]:
    created: Optional[date] = None
    finished: Optional[date] = None
    while True:
        m = DATE_TAG_RE.search(body)
        if not m:
            break
        value = date.fromisoformat(m.group(2))
        if m.group(1) == "created":
            created = value
        else:
            finished = value
        body = body[: m.start()] + body[m.end() :]
    return body.rstrip(), created, finished


def _extract_ticket(body: str) -> Tuple[str, Optional[str]]:
    m = TICKET_TRAILING_RE.search(body)
    if not m:
        return body, None
    return body[: m.start()].rstrip(), m.group(1)


def _extract_details(body: str) -> Tuple[str, Optional[str]]:
    m = DETAILS_TRAILING_RE.search(body)
    if not m:
        return body, None
    return body[: m.start()].rstrip(), m.group(1)


def parse_line(line: str) -> Optional[Task]:
    match = LINE_RE.match(line)
    if not match:
        return None
    status = MARKER_TO_STATUS[match.group("marker")]
    body, created, finished = _extract_dates(match.group("body"))
    body, ticket = _extract_ticket(body)
    body, details = _extract_details(body)
    return Task(
        status=status,
        title=body.strip(),
        details=details,
        ticket=ticket,
        created=created,
        finished=finished,
    )


def format_line(task: Task) -> str:
    parts = [f"- [{MARKERS[task.status]}] {task.title}"]
    if task.details is not None:
        parts.append(f"({task.details})")
    if task.ticket is not None:
        parts.append(f"#{task.ticket}")
    if task.created is not None:
        parts.append(f"@created:{task.created.isoformat()}")
    if task.finished is not None:
        parts.append(f"@finished:{task.finished.isoformat()}")
    return " ".join(parts)


ADD_TICKET_RE = re.compile(rf"\s+#({TICKET_TOKEN})\b")
ADD_DETAILS_RE = re.compile(r"\s+\(([^()]*)\)")


def parse_add_text(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    ticket: Optional[str] = None
    details: Optional[str] = None
    m = ADD_TICKET_RE.search(text)
    if m:
        ticket = m.group(1)
        text = text[: m.start()] + text[m.end() :]
    m = ADD_DETAILS_RE.search(text)
    if m:
        details = m.group(1)
        text = text[: m.start()] + text[m.end() :]
    return text.strip(), ticket, details
