from datetime import date

from kanibal.models import Status, Task
from kanibal.render import format_list


def test_empty_list_renders_to_empty_string():
    assert format_list([]) == ""


def test_minimal_task_renders_with_marker_and_title():
    task = Task(status=Status.TODO, title="instalacja istio na JCB")
    assert format_list([task]) == "[ ] instalacja istio na JCB"


def test_ticket_renders_as_leading_token_in_title_without_hash():
    task = Task(status=Status.DONE, title="PROD switch", ticket="D164")
    assert format_list([task]) == "[x] D164 PROD switch"


def test_details_render_in_parens_after_title():
    task = Task(
        status=Status.WORKING,
        title="skasowac pozostalosci falco",
        details="repo, joby, alerty, role?",
    )
    assert format_list([task]) == (
        "[/] skasowac pozostalosci falco (repo, joby, alerty, role?)"
    )


def test_dates_are_hidden_in_rendered_output():
    task = Task(
        status=Status.DONE,
        title="x",
        ticket="D164",
        created=date(2026, 5, 19),
        finished=date(2026, 5, 21),
    )
    assert format_list([task]) == "[x] D164 x"


def test_multi_task_render_preserves_order():
    tasks = [
        Task(
            status=Status.WORKING,
            title="skasowac pozostalosci falco",
            details="repo, joby, alerty, role?",
        ),
        Task(status=Status.DONE, title="PROD switch", ticket="D164"),
        Task(status=Status.DONE, title="analiza dlaczego /keys wyrzuca CORS 403 problem"),
        Task(status=Status.TODO, title="instalacja istio na JCB"),
    ]
    assert format_list(tasks) == (
        "[/] skasowac pozostalosci falco (repo, joby, alerty, role?)\n"
        "[x] D164 PROD switch\n"
        "[x] analiza dlaczego /keys wyrzuca CORS 403 problem\n"
        "[ ] instalacja istio na JCB"
    )
