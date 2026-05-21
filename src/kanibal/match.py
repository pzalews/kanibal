from __future__ import annotations

from typing import Sequence

from kanibal.models import Task


class MatchError(Exception):
    pass


class NoMatch(MatchError):
    def __init__(self, query: str):
        super().__init__(f'No task matches "{query}".')
        self.query = query


class AmbiguousMatch(MatchError):
    def __init__(self, query: str, candidates: Sequence[Task]):
        super().__init__(f'Ambiguous match for "{query}" — {len(candidates)} tasks.')
        self.query = query
        self.candidates = list(candidates)


def resolve(query: str, pool: Sequence[Task]) -> Task:
    if not pool:
        raise NoMatch(query)

    ticket = query[1:] if query.startswith("#") else query
    for task in pool:
        if task.ticket is not None and task.ticket == ticket:
            return task

    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(pool):
            return pool[idx]

    needle = query.casefold()
    matches = [t for t in pool if needle in t.title.casefold()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise AmbiguousMatch(query, matches)
    raise NoMatch(query)
