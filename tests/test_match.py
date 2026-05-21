import pytest

from kanibal.match import AmbiguousMatch, NoMatch, resolve
from kanibal.models import Status, Task


def _task(title: str, ticket: str | None = None, status: Status = Status.TODO) -> Task:
    return Task(status=status, title=title, ticket=ticket)


def test_exact_ticket_match_with_hash():
    pool = [_task("one", "D164"), _task("two")]
    assert resolve("#D164", pool) is pool[0]


def test_exact_ticket_match_without_hash():
    pool = [_task("one", "D164"), _task("two")]
    assert resolve("D164", pool) is pool[0]


def test_line_number_match():
    pool = [_task("one"), _task("two"), _task("three")]
    assert resolve("2", pool) is pool[1]


def test_fuzzy_substring_match_case_insensitive():
    pool = [_task("instalacja istio na JCB"), _task("PROD switch")]
    assert resolve("istio", pool) is pool[0]
    assert resolve("ISTIO", pool) is pool[0]


def test_ticket_takes_priority_over_fuzzy():
    # "D" as a fuzzy substring also matches "D164" in title — but ticket lookup
    # is tried first and finds nothing (no ticket equals "D"), so we fall back
    # to fuzzy. This test pins behavior: an exact ticket beats fuzzy.
    pool = [_task("alpha", "D164"), _task("contains D164 in title")]
    assert resolve("D164", pool) is pool[0]


def test_line_number_takes_priority_over_fuzzy():
    pool = [_task("2 is the magic number"), _task("two"), _task("three")]
    # "2" could fuzzy-match the first task's title but line number wins
    assert resolve("2", pool) is pool[1]


def test_no_match_raises():
    pool = [_task("alpha"), _task("beta")]
    with pytest.raises(NoMatch):
        resolve("zeta", pool)


def test_ambiguous_fuzzy_raises_with_candidates():
    pool = [_task("PROD switch", "D164"), _task("switch DNS")]
    with pytest.raises(AmbiguousMatch) as exc:
        resolve("switch", pool)
    assert list(exc.value.candidates) == pool


def test_line_number_out_of_range_falls_through_to_fuzzy():
    pool = [_task("99 problems"), _task("just two")]
    # "99" is out of range as a line number, so falls through to fuzzy match
    assert resolve("99", pool) is pool[0]


def test_empty_pool_raises_no_match():
    with pytest.raises(NoMatch):
        resolve("anything", [])
