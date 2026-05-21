from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kanibal import dates
from kanibal.cli import app

runner = CliRunner()


@pytest.fixture
def task_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "kanibal.md"
    monkeypatch.setenv("KANIBAL_FILE", str(path))
    return path


@pytest.fixture
def fixed_today(monkeypatch):
    def _set(value: date):
        monkeypatch.setattr(dates, "today", lambda: value)

    return _set


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def test_kanibal_no_args_on_missing_file_is_empty(task_file):
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert result.stdout == "\n" or result.stdout == ""


def test_add_creates_file_with_todo_marker_and_today_created(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    result = runner.invoke(app, ["add", "instalacja istio na JCB"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == "- [ ] instalacja istio na JCB @created:2026-05-21\n"


def test_add_parses_inline_ticket_and_details(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    result = runner.invoke(
        app, ["add", "PROD switch #D164 (repo, joby, alerty)"]
    )
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == (
        "- [ ] PROD switch (repo, joby, alerty) #D164 @created:2026-05-21\n"
    )


def test_start_transitions_todo_to_working(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text("- [ ] instalacja istio na JCB @created:2026-05-21\n")
    result = runner.invoke(app, ["start", "istio"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == "- [/] instalacja istio na JCB @created:2026-05-21\n"


def test_done_sets_finished_today_and_done_marker(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text("- [/] PROD switch #D164 @created:2026-05-19\n")
    result = runner.invoke(app, ["done", "D164"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == (
        "- [x] PROD switch #D164 @created:2026-05-19 @finished:2026-05-21\n"
    )


def test_start_clears_finished_date(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text(
        "- [x] PROD switch #D164 @created:2026-05-19 @finished:2026-05-21\n"
    )
    result = runner.invoke(app, ["start", "D164"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == "- [/] PROD switch #D164 @created:2026-05-19\n"


def test_postpone_transitions_and_clears_finished(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text(
        "- [x] PROD switch #D164 @created:2026-05-19 @finished:2026-05-21\n"
    )
    result = runner.invoke(app, ["postpone", "D164"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == "- [?] PROD switch #D164 @created:2026-05-19\n"


def test_postpone_no_args_lists_postponed_only(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text(
        "- [ ] alpha @created:2026-05-21\n"
        "- [?] beta #B-1 @created:2026-05-10\n"
        "- [?] gamma @created:2026-05-12\n"
    )
    result = runner.invoke(app, ["postpone"])
    assert result.exit_code == 0
    assert result.stdout.strip().splitlines() == [
        "[?] B-1 beta",
        "[?] gamma",
    ]


def test_resume_moves_postponed_back_to_todo(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text("- [?] beta #B-1 @created:2026-05-10\n")
    result = runner.invoke(app, ["resume", "B-1"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == "- [ ] beta #B-1 @created:2026-05-10\n"


def test_resume_only_searches_postponed_pool(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    # "switch" appears in two tasks but only one is postponed → no ambiguity
    task_file.write_text(
        "- [ ] PROD switch #D164 @created:2026-05-20\n"
        "- [?] switch DNS @created:2026-05-10\n"
    )
    result = runner.invoke(app, ["resume", "switch"])
    assert result.exit_code == 0, result.stdout
    assert _read(task_file) == (
        "- [ ] PROD switch #D164 @created:2026-05-20\n"
        "- [ ] switch DNS @created:2026-05-10\n"
    )


def test_list_hides_postponed_and_old_done(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text(
        "# Tasks\n"
        "- [/] working_a @created:2026-05-20\n"
        "- [x] done_today @created:2026-05-20 @finished:2026-05-21\n"
        "- [x] done_yesterday @created:2026-05-19 @finished:2026-05-20\n"
        "- [ ] todo_a @created:2026-05-21\n"
        "- [?] postponed_a @created:2026-05-01\n"
    )
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert result.stdout.strip().splitlines() == [
        "[/] working_a",
        "[x] done_today",
        "[ ] todo_a",
    ]


def test_ambiguous_match_errors_and_lists_candidates(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text(
        "- [/] PROD switch #D164 @created:2026-05-20\n"
        "- [ ] switch DNS @created:2026-05-21\n"
    )
    result = runner.invoke(app, ["done", "switch"])
    assert result.exit_code != 0
    out = result.stdout
    assert "Ambiguous" in out
    assert "D164" in out
    assert "switch DNS" in out


def test_no_match_errors(task_file, fixed_today):
    fixed_today(date(2026, 5, 21))
    task_file.write_text("- [ ] alpha @created:2026-05-21\n")
    result = runner.invoke(app, ["done", "nothing"])
    assert result.exit_code != 0
    assert "No task" in result.stdout
