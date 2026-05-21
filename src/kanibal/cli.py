from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import typer

from kanibal import dates
from kanibal.match import AmbiguousMatch, NoMatch, resolve
from kanibal.models import Status, Task
from kanibal.parser import parse_add_text
from kanibal.render import format_list
from kanibal.storage import Document, load

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode=None,
)


def _task_file() -> Path:
    override = os.environ.get("KANIBAL_FILE")
    if override:
        return Path(override)
    return Path.home() / "kanibal.md"


def _visible_for_list(doc: Document) -> List[Task]:
    today = dates.today()
    out: List[Task] = []
    for t in doc.tasks:
        if t.status in (Status.TODO, Status.WORKING):
            out.append(t)
        elif t.status is Status.DONE and t.finished == today:
            out.append(t)
    return out


def _postponed(doc: Document) -> List[Task]:
    return [t for t in doc.tasks if t.status is Status.POSTPONED]


def _resolve_or_die(query: str, pool: List[Task]) -> Task:
    try:
        return resolve(query, pool)
    except NoMatch as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)
    except AmbiguousMatch as e:
        typer.echo("Ambiguous — multiple matches:")
        for i, cand in enumerate(e.candidates, start=1):
            typer.echo(f"  {i}  {format_list([cand])}")
        typer.echo("Refine your match, e.g. by ticket.")
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _do_list()


@app.command("list")
def list_cmd() -> None:
    """Show today's tasks (todo + working + done-today)."""
    _do_list()


def _do_list() -> None:
    doc = load(_task_file())
    typer.echo(format_list(_visible_for_list(doc)))


@app.command()
def add(text: str) -> None:
    """Add a new task. Inline `#TICKET` and `(details)` are parsed from text."""
    title, ticket, details = parse_add_text(text)
    if not title:
        typer.echo("Refusing to add a task with empty title.")
        raise typer.Exit(code=1)
    doc = load(_task_file())
    doc.add_task(
        Task(
            status=Status.TODO,
            title=title,
            ticket=ticket,
            details=details,
            created=dates.today(),
        )
    )
    doc.save()


@app.command()
def start(match: str) -> None:
    """Transition a task to working ([/])."""
    doc = load(_task_file())
    task = _resolve_or_die(match, _visible_for_list(doc))
    task.status = Status.WORKING
    task.finished = None
    doc.replace_task(task)
    doc.save()


@app.command()
def done(match: str) -> None:
    """Transition a task to done ([x]) and stamp @finished:today."""
    doc = load(_task_file())
    task = _resolve_or_die(match, _visible_for_list(doc))
    task.status = Status.DONE
    task.finished = dates.today()
    doc.replace_task(task)
    doc.save()


@app.command()
def postpone(match: Optional[str] = typer.Argument(None)) -> None:
    """With <match>: transition to postponed ([?]). Without args: list postponed."""
    doc = load(_task_file())
    if match is None:
        typer.echo(format_list(_postponed(doc)))
        return
    task = _resolve_or_die(match, _visible_for_list(doc))
    task.status = Status.POSTPONED
    task.finished = None
    doc.replace_task(task)
    doc.save()


@app.command()
def resume(match: str) -> None:
    """Bring a postponed task back to todo ([ ])."""
    doc = load(_task_file())
    task = _resolve_or_die(match, _postponed(doc))
    task.status = Status.TODO
    doc.replace_task(task)
    doc.save()
