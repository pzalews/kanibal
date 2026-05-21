from __future__ import annotations

from typing import Sequence

from kanibal.models import MARKERS, Task


def _render_task(task: Task) -> str:
    title = task.title if task.ticket is None else f"{task.ticket} {task.title}"
    line = f"[{MARKERS[task.status]}] {title}"
    if task.details is not None:
        line += f" ({task.details})"
    return line


def format_list(tasks: Sequence[Task]) -> str:
    return "\n".join(_render_task(t) for t in tasks)
