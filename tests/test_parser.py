from datetime import date

from kanibal.models import Status, Task
from kanibal.parser import format_line, parse_add_text, parse_line


def test_parse_minimal_todo_line():
    line = "- [ ] instalacja istio na JCB"
    task = parse_line(line)
    assert task == Task(
        status=Status.TODO,
        title="instalacja istio na JCB",
        details=None,
        ticket=None,
        created=None,
        finished=None,
    )


def test_parse_full_line():
    line = (
        "- [x] PROD switch (repo, joby, alerty) #D164 "
        "@created:2026-05-19 @finished:2026-05-21"
    )
    assert parse_line(line) == Task(
        status=Status.DONE,
        title="PROD switch",
        details="repo, joby, alerty",
        ticket="D164",
        created=date(2026, 5, 19),
        finished=date(2026, 5, 21),
    )


def test_parse_working_and_postponed_markers():
    assert parse_line("- [/] x").status is Status.WORKING
    assert parse_line("- [?] x").status is Status.POSTPONED


def test_parse_non_task_line_returns_none():
    assert parse_line("# Tasks") is None
    assert parse_line("") is None
    assert parse_line("just some prose") is None
    assert parse_line("- [z] bad marker") is None


def test_parse_only_ticket():
    task = parse_line("- [ ] PROD switch #D164")
    assert task.ticket == "D164"
    assert task.title == "PROD switch"
    assert task.details is None


def test_parse_only_details():
    task = parse_line("- [ ] skasowac falco (repo, joby, alerty, role?)")
    assert task.title == "skasowac falco"
    assert task.details == "repo, joby, alerty, role?"


def test_format_minimal_line():
    task = Task(status=Status.TODO, title="instalacja istio na JCB")
    assert format_line(task) == "- [ ] instalacja istio na JCB"


def test_format_full_line():
    task = Task(
        status=Status.DONE,
        title="PROD switch",
        details="repo, joby, alerty",
        ticket="D164",
        created=date(2026, 5, 19),
        finished=date(2026, 5, 21),
    )
    assert format_line(task) == (
        "- [x] PROD switch (repo, joby, alerty) #D164 "
        "@created:2026-05-19 @finished:2026-05-21"
    )


def test_roundtrip_all_markers_and_field_combinations():
    cases = [
        "- [ ] instalacja istio na JCB",
        "- [/] skasowac falco (repo, joby, alerty, role?) @created:2026-05-20",
        "- [x] PROD switch #D164 @created:2026-05-19 @finished:2026-05-21",
        "- [?] cleanup legacy gateway #OLD-1 @created:2026-04-10",
        "- [ ] noop with ticket only #T-1",
        "- [ ] noop with details only (a, b, c)",
    ]
    for line in cases:
        task = parse_line(line)
        assert task is not None, line
        assert format_line(task) == line, line


def test_parse_add_text_extracts_ticket_and_details():
    title, ticket, details = parse_add_text(
        "PROD switch #D164 (repo, joby, alerty)"
    )
    assert title == "PROD switch"
    assert ticket == "D164"
    assert details == "repo, joby, alerty"


def test_parse_add_text_plain_title():
    assert parse_add_text("instalacja istio na JCB") == (
        "instalacja istio na JCB",
        None,
        None,
    )


def test_parse_add_text_ticket_only():
    assert parse_add_text("PROD switch #D164") == ("PROD switch", "D164", None)


def test_parse_add_text_details_only():
    assert parse_add_text("skasowac falco (repo, joby)") == (
        "skasowac falco",
        None,
        "repo, joby",
    )
