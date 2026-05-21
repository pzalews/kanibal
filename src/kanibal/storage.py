from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from kanibal.models import Task
from kanibal.parser import format_line, parse_line


@dataclass
class Document:
    path: Path
    lines: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    trailing_newline: bool = True

    def replace_task(self, task: Task) -> None:
        assert task.line_index is not None, "task has no line_index"
        self.lines[task.line_index] = format_line(task)

    def add_task(self, task: Task) -> None:
        if self.tasks:
            insert_at = self.tasks[-1].line_index + 1
        else:
            insert_at = len(self.lines)
        self.lines.insert(insert_at, format_line(task))
        task.line_index = insert_at
        self.tasks.append(task)
        self.trailing_newline = True  # always end with newline after a write

    def save(self) -> None:
        content = "\n".join(self.lines)
        if self.trailing_newline and self.lines:
            content += "\n"
        elif not self.lines:
            content = ""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            prefix=self.path.name + ".",
            suffix=".tmp",
            dir=str(self.path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise


def load(path: Path) -> Document:
    if not path.exists():
        return Document(path=path)
    text = path.read_text(encoding="utf-8")
    trailing_newline = text.endswith("\n")
    raw = text.split("\n")
    if trailing_newline:
        raw = raw[:-1]  # drop the empty string after final \n
    tasks: List[Task] = []
    for idx, line in enumerate(raw):
        parsed = parse_line(line)
        if parsed is not None:
            parsed.line_index = idx
            tasks.append(parsed)
    return Document(
        path=path, lines=raw, tasks=tasks, trailing_newline=trailing_newline
    )
