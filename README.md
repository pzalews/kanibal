# kanibal

A minimal personal Kanban CLI, backed by a single markdown file.

`kanibal` shows you what matters today: every task that's `todo` or `working`,
plus anything you finished today. Postponed tasks are hidden until you ask for
them.

## Install

Recommended — install globally with [pipx](https://pipx.pypa.io/) so `kanibal`
is always on your PATH:

```bash
pipx install --editable /path/to/kanibal
```

Editable mode means edits to the source take effect immediately, no reinstall
needed.

Alternatively, develop against a project-local venv:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Either path provides a `kanibal` console script.

## Usage

```text
$ kanibal                                       # list today's tasks
$ kanibal add "PROD switch #D164 (repo, joby)"  # new todo
$ kanibal start D164                            # → working
$ kanibal done D164                             # → done, finished today
$ kanibal postpone D164                         # → postponed (hidden from list)
$ kanibal postpone                              # list postponed tasks
$ kanibal resume D164                           # bring postponed back to todo
```

`kanibal` with no arguments is the same as `kanibal list`. The default list
shows everything that is **todo** or **working**, plus tasks **done today**.
**Postponed** tasks are never in the default list — see them with
`kanibal postpone` (no args).

### Matching a task

Commands that take `<match>` (`start`, `done`, `postpone`, `resume`) accept any
of:

1. **Ticket** — `kanibal done D164` or `kanibal done #D164`
2. **Line number** — 1-based index into the listing, e.g. `kanibal start 3`
3. **Fuzzy title** — case-insensitive substring of the title, e.g.
   `kanibal done istio`

Resolution tries them in that order. An ambiguous fuzzy match prints every
candidate and exits non-zero so you can re-run with something more specific.
`resume` only searches postponed tasks, so a fuzzy match there won't collide
with active work.

## File format

Tasks live in `~/kanibal.md` (override with `KANIBAL_FILE`). One task per line,
GFM checkbox syntax with inline trailing tags:

```text
- [<marker>] <title> (<details>) #<TICKET> @created:YYYY-MM-DD @finished:YYYY-MM-DD
```

| marker | status     |
|--------|------------|
| `[ ]`  | todo       |
| `[/]`  | working    |
| `[x]`  | done       |
| `[?]`  | postponed  |

Everything after the title is optional. Non-task lines in the file (headings,
blank lines, free-form notes) are preserved untouched on save. Writes are
atomic (tempfile + `os.replace`) so a crashed `kanibal` will never corrupt the
file.

Example file:

```markdown
# Tasks

- [/] skasowac pozostalosci falco (repo, joby, alerty, role?) @created:2026-05-20
- [x] PROD switch #D164 @created:2026-05-19 @finished:2026-05-21
- [ ] instalacja istio na JCB @created:2026-05-21
- [?] cleanup legacy gateway #OLD-1 @created:2026-04-10
```

`kanibal` (run on 2026-05-21) renders that as:

```text
[/] skasowac pozostalosci falco (repo, joby, alerty, role?)
[x] D164 PROD switch
[ ] instalacja istio na JCB
```

The postponed entry is hidden; the done entry is shown because it was finished
today.

## Tests

```bash
.venv/bin/pytest
```

50 tests cover line parsing/formatting round-trips, storage with non-task line
preservation, atomic writes, match resolution (ticket/line/fuzzy + ambiguity),
list filtering by date, and every CLI subcommand end-to-end.
