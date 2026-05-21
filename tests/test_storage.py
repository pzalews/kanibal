from datetime import date
from pathlib import Path

from kanibal.models import Status, Task
from kanibal.storage import load


def test_load_missing_file_returns_empty_doc(tmp_path: Path):
    doc = load(tmp_path / "kanibal.md")
    assert doc.tasks == []
    assert doc.lines == []


def test_load_empty_file_returns_empty_doc(tmp_path: Path):
    path = tmp_path / "k.md"
    path.write_text("")
    doc = load(path)
    assert doc.tasks == []


def test_load_parses_task_lines_and_records_line_indices(tmp_path: Path):
    path = tmp_path / "k.md"
    path.write_text(
        "# Tasks\n"
        "\n"
        "- [ ] instalacja istio na JCB @created:2026-05-21\n"
        "free text note\n"
        "- [x] PROD switch #D164 @created:2026-05-19 @finished:2026-05-21\n"
    )
    doc = load(path)
    assert len(doc.tasks) == 2
    assert doc.tasks[0].title == "instalacja istio na JCB"
    assert doc.tasks[0].status is Status.TODO
    assert doc.tasks[0].line_index == 2
    assert doc.tasks[1].ticket == "D164"
    assert doc.tasks[1].finished == date(2026, 5, 21)
    assert doc.tasks[1].line_index == 4


def test_save_preserves_non_task_lines(tmp_path: Path):
    path = tmp_path / "k.md"
    original = (
        "# Tasks\n"
        "\n"
        "- [ ] one @created:2026-05-21\n"
        "some prose\n"
        "- [/] two #D164 @created:2026-05-20\n"
    )
    path.write_text(original)
    doc = load(path)
    doc.save()
    assert path.read_text() == original


def test_replace_task_writes_new_line_at_same_index(tmp_path: Path):
    path = tmp_path / "k.md"
    path.write_text(
        "# Tasks\n"
        "- [ ] one @created:2026-05-21\n"
        "- [ ] two @created:2026-05-21\n"
    )
    doc = load(path)
    task = doc.tasks[1]
    task.status = Status.DONE
    task.finished = date(2026, 5, 22)
    doc.replace_task(task)
    doc.save()
    assert path.read_text() == (
        "# Tasks\n"
        "- [ ] one @created:2026-05-21\n"
        "- [x] two @created:2026-05-21 @finished:2026-05-22\n"
    )


def test_add_task_appends_after_last_task_line(tmp_path: Path):
    path = tmp_path / "k.md"
    path.write_text(
        "# Tasks\n"
        "- [ ] one @created:2026-05-21\n"
        "\n"
        "trailing prose\n"
    )
    doc = load(path)
    new_task = Task(
        status=Status.TODO,
        title="two",
        created=date(2026, 5, 22),
    )
    doc.add_task(new_task)
    doc.save()
    assert path.read_text() == (
        "# Tasks\n"
        "- [ ] one @created:2026-05-21\n"
        "- [ ] two @created:2026-05-22\n"
        "\n"
        "trailing prose\n"
    )
    assert new_task.line_index == 2


def test_add_task_to_empty_file_creates_it(tmp_path: Path):
    path = tmp_path / "k.md"
    doc = load(path)
    doc.add_task(
        Task(status=Status.TODO, title="first", created=date(2026, 5, 21))
    )
    doc.save()
    assert path.read_text() == "- [ ] first @created:2026-05-21\n"


def test_save_writes_atomically_via_tempfile(tmp_path: Path):
    """If save fails mid-write, the original file should remain intact."""
    path = tmp_path / "k.md"
    path.write_text("- [ ] one @created:2026-05-21\n")
    doc = load(path)
    doc.save()
    # The file should exist and be readable as the same content.
    assert path.read_text() == "- [ ] one @created:2026-05-21\n"
    # No leftover temp files in the directory.
    siblings = [p.name for p in tmp_path.iterdir()]
    assert siblings == ["k.md"]
