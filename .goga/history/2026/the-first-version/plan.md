# Plan: `the-first-version: first implementation of the comprehensive-review presets tool`

Compiled from `.goga/history/2026/the-first-version/design.md` (verified by `design-review`, goga 2.0.2)
into `goga_tool_complex_build/CODEMANIFEST` (read-only contract).

---

## Purpose

Implement the project's first cell `goga_tool_complex_build` from its CODEMANIFEST: the hook-only goga tool
package that contributes four comprehensive-review presets to the `config / amend_config` action and guards
the authored `build.review.strategy`.

After implementation the package provides:

- `goga_tool_complex_build/registration.py` with both contract Routines — `register_hooks(hooks)` and
  `review_presets(context)` — exactly per the CODEMANIFEST algorithms;
- a facade `goga_tool_complex_build/__init__.py` re-exporting both by identity through
  `__all__ = ["register_hooks", "review_presets"]` (functionally required: a facade without a callable
  `register_hooks` is a **quiet skip** — the tool would silently never register);
- a full pytest suite (16 design-verified scenarios) plus ruff-clean source and tests;
- `pyproject.toml` test extra extended with `goga>=2.0` (the single goga requirement, test-only).

Strategy: TDD per task (contract tests first), REPL-driven development with hot reloading and migration of
verified code into source files, ruff lint + format enforced at every stage and before every local commit,
all development inside the `/opt/project` venv (outside the project tree).

---

## Context

### Contract Surface

**Entity: `register_hooks(hooks: HookRegistrar)`**
- Type: `function` (Routine — no methods/properties)
- Declared `location`: `goga_tool_complex_build/registration.py`
- Facade obligation: importable from `goga_tool_complex_build` (re-exported via `__all__`)
- Mutations: none
- Semantic requirements (from CODEMANIFEST annotation, transferred verbatim):
  - Subscribe the tool's single review-presets hook to the configuration amendment action.
  - `hooks`: platform registration surface delivered to the facade callback.
  - Algorithm:
    1. Subscribe `review_presets` to the config / amend_config address under the hook name
       review_presets, using the subscribe operation of `hooks` defined in `hook_registration`
       → one `subscribe("config", "amend_config", "review_presets", review_presets)` call; return `None`.
  - Requirements: hook name stays unique per tool per address.
  - Constraints: subscribe to no other domain action; do not validate any configuration leaf.
- Design-verified behavior: returns `None`; invalid envelopes are refused by the registrar **as data with a
  log warning, never raised** (unreachable here — address is declared, name non-empty and used once, hook is
  the module-level routine); the `hooks` surface is tool-scoped (`tool="complex-build"` assigned by the
  platform from the package name — the routine never names its own tool identity).
- Imported dependencies: none at runtime — `HookRegistrar` is referenced under `TYPE_CHECKING` only.
- Annotation context: global annotations (hook-only cell, TYPE_CHECKING-only platform types, facade
  re-export through `__all__`, apply-where-silent only) → type annotation.

**Entity: `review_presets(context: ConfigAmendment)`**
- Type: `function` (Routine — no methods/properties)
- Declared `location`: `goga_tool_complex_build/registration.py`
- Facade obligation: importable from `goga_tool_complex_build` (re-exported via `__all__`)
- Mutations: none
- Semantic requirements (from CODEMANIFEST annotation, transferred verbatim):
  - Contribute the four comprehensive-review presets and guard the authored strategy.
  - `context`: read-and-amend view over the authored configuration, delivered per `config_amendment`.
  - Algorithm:
    1. Read the authored leaf `build.review.strategy` from the configuration of `context`; absent branches
       read as absent:
       `config = context.config` → `build = config.build` (`BuildConfig | None`) →
       `review = build.review if build is not None else None` →
       `strategy = review.strategy if review is not None else None` (`str | None`).
    2. If the authored value is present (`is not None`) and is not `"full"` — raise `ValueError` whose
       message names the path `build.review.strategy` and never the authored value. Fixed message literal:
       `"authored value at build.review.strategy conflicts with the tool's purpose; "
       "remove the authored strategy or uninstall the tool"`.
    3. Buffer four apply-where-silent amendments through `context.set(path, value)`, in order:
       `("build.review.strategy", "full")`, `("build.review.max_iterations", 5)`,
       `("build.review.additional.patience", 2)`, `("build.review.additional.max_iterations", 3)`.
       Return `None`; the merge layer resolves authored-wins later.
  - Requirements:
    - The guard raise of step 2 happens before any amendment is buffered.
    - The guard message is the fixed strategy-conflict message (above) — do not reword, interpolate
      values, or add tool/action names (the platform wrapper supplies those).
    - Amendments are unconditional — the deliberate reads of the configuration are the guard leaf of
      step 1 only.
    - Authored-wins is owned by the merge layer — never re-derived here.
    - The exact write footprint is the four leaf paths of step 3 and nothing else.
  - Constraints: never use the override form of amendment (`force` is never called); never print or embed
    configuration values in any output or error message; do not validate any leaf beyond the strategy guard.
- Design-verified behavior: the platform delivers only declared offered names by keyword
  (`{"context": proxy}`); the delivery proxy passes reads and `set` calls through and blocks attribute
  writes; absent/half-present branches read as `None` without `AttributeError`; authored emptiness (`""`)
  and non-string scalars count as present-and-conflicting; on conflict the platform wraps the raise as
  `ValueError("hook review_presets of tool complex-build failed on config.amend_config: …")` and discards
  the tool's whole contribution; on success the merge yields effective `strategy=full, max_iterations=5,
  patience=2, additional.max_iterations=3` on a silent base with 4 applied records and the value-free
  summary lines (pinned in the integration tests below).
- Imported dependencies: none at runtime — `ConfigAmendment` is referenced under `TYPE_CHECKING` only.
- Annotation context: global annotations (as above) → type annotation.

**Facade (from global annotations):** `__init__.py` re-exports the contract API through
`__all__ = ["register_hooks", "review_presets"]` (relative import, re-export by identity) and stays
import-clean with or without goga installed.

### Entity Interaction and Data Flow (verbatim from the design — verified against goga 2.0.2)

```
                         goga platform (runtime, not a project cell)
   ┌──────────────────────────────────────────────────────────────────────┐
   │ enumerate_tool_packages() ──► goga_tool_complex_build (facade import)│
   │        tool identity: complex-build (from package name)              │
   │                                                                      │
   │  HookRegistrar(tool="complex-build")                                 │
   │        ▲ call_register_hooks imports the facade,                     │
   │        │ calls facade.register_hooks(registrar)                      │
   │        ▼                                                             │
   │ subscribe("config","amend_config","review_presets", review_presets) │
   │        │ accepted: address declared in catalog, error_class="hard"   │
   │        ▼                                                             │
   │  amend_config checkpoint (load moment of .goga/config.yml):          │
   │    ConfigAmendment(config=read_only_snapshot(authored))              │
   │        ── wrap_context ──► delivery proxy (reads/calls pass,         │
   │                             attribute writes blocked)                │
   │    build_hook_arguments(review_presets, proxy, self_context)         │
   │        ──► {"context": proxy}  (only declared offered names)         │
   └──────────────┬───────────────────────────────────────────────────────┘
                  │ review_presets(context)  ── cell under design ──
                  ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │ goga_tool_complex_build            Imports: none (single-node graph) │
   │                                                                     │
   │  registration.py                                                    │
   │    register_hooks(hooks)  ── one subscribe call ─────────────────┐  │
   │    review_presets(context)                                       │  │
   │      1. read  context.config.build.review.strategy (None-chain)  │  │
   │      2. guard  present and ≠ "full" ──► ValueError (path only)   │  │
   │      3. set ×4  strategy=full, max_iterations=5,                 │  │
   │                 patience=2, additional.max_iterations=3          │  │
   │                              buffer: PathAmendment(intent="set") │  │
   │  __init__.py  re-export: __all__ = [register_hooks, review_presets]│
   └─────────────────────────────────────────────────────────────────────┘
                  │ commit (only if every hook of the tool returned)
                  ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │ merge_config_amendments(authored, [ToolAmendment])                  │
   │   VALIDATE paths/types ─► RESOLVE authored-wins for "set" ─►        │
   │   COMPOSE (materialize absent branches) ─► COLLECT applied records  │
   │   ──► ConfigOverlay: effective config + summary lines (no values)   │
   └─────────────────────────────────────────────────────────────────────┘
```

**Scenario A — registration (once per run, lazily at the first hook checkpoint of a command):**
platform enumerates installed `goga_tool_*` packages (alphabetical, no imports) → imports the facade
`goga_tool_complex_build` (the single fatal case is a broken facade import) → reads `register_hooks` off the
facade → calls it with `HookRegistrar(tool="complex-build")` → the routine performs exactly one
`subscribe("config", "amend_config", "review_presets", review_presets)` → the registrar resolves the address
against `declared_actions` (accepted: `Action(domain="config", name="amend_config", error_class="hard")`) and
appends one `Subscription`. Registration is never cached — package edits apply from the next run.

**Scenario B — amendment delivery (at the load moment of `.goga/config.yml` on every config-consuming
surface):** the loader produces the authored `ProjectConfig` → the checkpoint builds a per-tool
`ConfigAmendment` over a deeply read-only snapshot of it → wraps it in the delivery proxy → projects the
call arguments (only `context`, by name) → calls `review_presets(context)` → the routine reads the strategy
chain, applies the guard, buffers four `set` amendments → on return, the tool's buffer commits as one
`ToolAmendment` (an empty buffer commits nothing) → the merge validates, resolves (authored-wins for `set`),
composes the effective configuration, and collects `AppliedAmendment` records → the caller prints the summary
lines to stderr (never values).

**Scenario C — strategy conflict:** as B, but the guard raises `ValueError` before any `set` is buffered →
the checkpoint catches it and re-raises `ValueError("hook review_presets of tool complex-build failed on
config.amend_config: <guard message>")` → the command stops; the tool's whole contribution (its view and
buffer) is discarded; nothing applies.

**Verified checkpoint summaries (Code Stack Trace):**
- `register_hooks` — facade discoverability: passed; address validity (`config.amend_config`, hard):
  passed; envelope validity (non-empty unique name, callable hook): passed; subscribe-arity/type alignment
  (`subscribe(domain: str, action: str, name: str, hook: Callable[..., object]) -> None`): passed.
- `review_presets` — hook-signature projection (`context` delivered by keyword): passed; read footprint
  (exactly the `build.review.strategy` chain): passed; guard semantics (present-and-≠`full` raises; `None`
  and `"full"` do not): passed; guard ordering (raise strictly before the first `set`): passed; write
  footprint (exactly the four leaf paths, intent `set` only, `force` never called): passed;
  value/path structural validity (all four resolve in the merge type tree with matching kinds): passed;
  authored-wins ownership (merge-layer responsibility; the hook never re-derives it): passed.

### Re-exports

- No `->Name: {}` embedding blocks exist in the CODEMANIFEST.
- Facade re-export obligation comes from the global annotation "The package facade re-exports the contract
  API through `__all__`": both Routines must be importable from `goga_tool_complex_build` by identity
  (`facade.register_hooks is registration.register_hooks`).

### Usages Context

- `conventions` — `.goga/usages/conventions.md`: mandatory Python engineering rules for this project
  (3.10+ compatibility, relative intra-package imports, Google-style docstrings, blank-line block
  formatting, logging policy, pyproject-based dependency management, and the full testing standard with
  validation commands). Bound to code AND tests; extracted in full into **Mandatory Rules** below.
- `hook_registration` — `.goga/usages/github/goga/hooks/registering-hooks.md`: the facade-callback
  contract for tool packages — `hooks.subscribe(domain, action, name, hook)` envelope, hook-name
  uniqueness per tool per address, offered-name parameter delivery (`context`, `self`), run timing
  (registration never cached), envelope rejection as data. Governs `register_hooks`.
- `config_amendment` — `.goga/usages/github/goga/config/registering-hooks.md`: the config domain action
  spec — the `config / amend_config` address (hard), the `ConfigAmendment` read-and-amend view
  (`config` reads, `set`/`force` buffering), silence markers (`None`, `{}`, `[]` vs authored `False`, `""`),
  merge rules (authored-wins for `set`, `force` beats `set`, later-tool-wins, tools mutually blind),
  failure treatment, and the value-free run summary. Governs `review_presets`.
- `goga_dependency` — `.goga/usages/cooks/goga-dependency.md`: dependency policy — empty runtime
  `[project].dependencies`, no runtime goga import, platform types under `typing.TYPE_CHECKING` only,
  goga declared exclusively in the `test` extra as `goga>=2.0` (floor at the platform line, no upper cap).
  Governs `registration.py` import structure and the `pyproject.toml` change.

### Imported Usages

- None — the cell has no `Imports` (single-node project graph, `dependencies: {}`).

### Local Usages

- `goga_tool_complex_build/.usages/comprehensive-review.md` — functional category: comprehensive-review
  presets for consumers. Status: **existing, verified current by design-review — no changes needed**.
  Related entities: both routines (consumer perspective). No creation/update tasks; **do not modify**.

### External Dependencies

- **goga platform (test-only)**: `goga>=2.0` in `[project.optional-dependencies].test`; installed goga
  2.0.2 provides `HookRegistrar` at `goga.hooks.tools.registration` and `ConfigAmendment` at
  `goga.config.hooks.amendments` (verified paths — neither is exported by the `goga.hooks`/`goga.config`
  facades). Delivery/merge primitives (`wrap_context`, `build_hook_arguments`,
  `merge_config_amendments`, `ConfigHooks`) are imported in tests from the platform modules where they
  live in the installed package (confirm exact modules interactively in the REPL — see REPL Cycle Rules).
- **Test stack**: `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-mock>=3.10`, `ruff>=0.15.0` (already declared
  in the test extra).
- **Tooling**: ruff is the project linter AND formatter; configuration already in `pyproject.toml`
  (`target-version = "py310"`, `line-length = 120`, rule set `E,W,F,I,N,UP,B,SIM,PL,PLR,C4,DTZ,PT,ARG,RUF,PTH,C90`,
  tests per-file-ignores, format: double quotes, space indent, LF endings).
- No runtime third-party dependencies (`[project].dependencies` stays `[]`).

---

## Facts

- Single-cell project: `goga schema` → one node, `dependencies: {}`; `goga lint` → `cells: 1, errors: 0`;
  `goga config language` → `python`.
- Both contract entities are Routines sharing one `location`: `goga_tool_complex_build/registration.py`
  (file does not exist yet).
- `goga_tool_complex_build/__init__.py` exists and is **empty** (0 bytes).
- `tests/` does not exist; no test has been written.
- `pyproject.toml`: `requires-python = ">=3.10"`; `dependencies = []`; test extra lacks `goga>=2.0`;
  ruff and pytest configuration already complete (including `tests/**` per-file-ignores and
  `testpaths = ["tests"]`).
- The `/opt/project` virtualenv **does not exist yet** — Task 1 creates it (all development runs there).
- Platform goga 2.0.2 is available; TYPE_CHECKING import paths verified:
  `from goga.hooks.tools.registration import HookRegistrar`,
  `from goga.config.hooks.amendments import ConfigAmendment`.
- The four header usages resolve to existing files (checked on disk).
- `goga_tool_complex_build/.usages/comprehensive-review.md` and `goga_tool_complex_build/CODEMANIFEST`
  are verified current by design-review — read-only for this implementation.
- Fixed literals verified empirically by design-review (scratch run reproduced every claimed value):
  the guard message, the four path/value pairs and their order, the merge outcomes
  (`full/5/2/3` silent → 4 applied; authored `full 5 4 0` → 2 applied), the exact summary lines, and the
  checkpoint error wrap `hook review_presets of tool complex-build failed on config.amend_config: …`.
- Ecosystem observation (informational): running goga commands in THIS workspace applies 3 amendments
  from the sibling platform tool `goga-tool-simple-build` to the workspace's own effective config. It does
  not affect this implementation; the integration tests assert with tool-name filters (`r.tool ==
  "complex-build"`) and the `/opt/project` venv keeps the test environment deterministic.

---

## Gap Analysis

- **Missing contract entities**: `register_hooks` and `review_presets` — `registration.py` absent entirely.
- **Missing facade exposure**: `__init__.py` is empty — no re-export, no `__all__` → platform quiet skip;
  the tool would silently never register.
- **Incorrect `location` placement**: none (no code exists yet).
- **API mismatches / behavioral mismatches**: none yet (greenfield).
- **Existing code that can be reused**: `__init__.py` (empty shell to be filled), `pyproject.toml`
  (complete except the missing `goga>=2.0` test-extra entry), `.goga/usages/*` (all present).
- **Test coverage gaps**: the entire suite — 16 design-verified scenarios (see Tasks 2–3).
- **Missing visibility in workspace or git**: `registration.py`, `tests/`, and the facade contents are to
  be created and committed; `CODEMANIFEST` and `.usages/` are present but untracked (leave for the
  pipeline — not this implementation's deliverables).

---

## Mandatory Rules

Extracted from the project convention `.goga/usages/conventions.md` (bound to this contract by
`Usages.conventions` — mandatory for all Python code in this project) and supplemented by the bound
language rules (`goga-cell-python`: type hints mandatory, PascalCase/snake_case, `__all__` facade) and the
general contract-oriented conventions (traceability, contract-to-test mapping, test classification).
These rules are **mandatory for every task**; conflicts resolve: contract first, facade obligations second,
these conventions next, language idioms last.

### M1. Coding Style Rules (strictly per `conventions`)

1. Python **3.10+ only**; all tool configuration lives in `pyproject.toml`.
2. **All development commands run inside the virtualenv at `/opt/project`** (outside the project tree;
   create it if missing — Task 1). Never create a project-local venv; never commit a venv.
3. **Imports**: relative imports for all intra-package references (`from .registration import …`);
   absolute imports only for stdlib and third-party. Forbidden: absolute import within the same package.
4. **Type hints are mandatory**; allowed shapes: `str`, `int`, `float`, `bool`, `list[T]`, `dict[str, T]`,
   `T | None`. Forbidden: `*args`, `**kwargs`, unparameterized `dict`/`list` (contract signatures are
   fixed: `(hooks: HookRegistrar)` and `(context: ConfigAmendment)` → `None`).
5. **Naming**: PascalCase for classes, snake_case for functions/methods/properties; names follow the
   contract vocabulary (`register_hooks`, `review_presets`).
6. **Docstrings — Google style, mandatory** for all public functions and classes: first line capitalized
   and ending with a period; `Args` section when parameters exist; `Raises` section when the code raises
   beyond built-in usage (the `review_presets` guard documents `ValueError`); `Returns` when a value is
   returned (both routines return `None` — document in prose, no `Returns` section needed).
7. **Block formatting**: inside function bodies, logical blocks are separated by **one blank line** —
   variable initialization from conditionals/loops, data preparation from processing, processing from
   the return.
8. **Dependencies**: every third-party library in `pyproject.toml` with a minimum version; test libraries
   only under `[project.optional-dependencies].test`. Runtime `[project].dependencies` stays empty.
9. **Logging**: this cell adds **no logger and no print** (design decision: the platform owns every
   observable output). Where logging exists elsewhere in the project: `logging` library, structured
   format, lowercase messages, contextual metadata, never secrets/configuration values.
10. **Never print or embed configuration values in any output or error message** (contract constraint —
    the guard message names the path `build.review.strategy` only).
11. Engineering principles: readable explicit code, predictable straightforward control flow, stable
    abstractions. No speculative generality; both routines are four-constant contributions.

### M2. Test Writing Rules (strictly per `conventions`)

1. **Framework**: pytest (+ pytest-cov, pytest-mock available). Test code is 3.10+ compatible.
2. **Structure — tests mirror the source directly**:
   `goga_tool_complex_build/registration.py` → `tests/test_registration.py`;
   `goga_tool_complex_build/__init__.py` → `tests/test_init.py`. Each test directory contains
   `__init__.py`. Shared fixtures in `tests/conftest.py`.
3. **Naming**: files `test_<module>.py`; functions `test_<what>_<scenario>`
   (e.g. `test_review_presets_buffers_four_presets_on_silent_config`); grouping `class Test<Component>:`
   (`TestRegisterHooks`, `TestReviewPresets`, `TestDelivery`, `TestInit`, `TestCheckpointIntegration`).
4. **Test types**: unit tests for every public function (main scenario + typical data); edge cases for
   empty inputs (`None`, `""`), boundary values (`0`, negative, very large), invalid types, expected
   exceptions via `pytest.raises`; integration tests **only** for interaction between modules/packages,
   placed directly in `tests/` (here: cell ↔ goga platform, inside the mirroring test modules per the
   design's file registry).
5. **Boundary tests**: for thresholds/ranges/type boundaries use `@pytest.mark.parametrize` with a table
   including each boundary (here: non-string strategy values `5`, `True`, `1.5`).
6. **Mocks — only at external boundaries**: pure logic tests are mock-free (fake/test-double objects such
   as `_FakeRegistrar` and `_RecordingAmendment` are hand-rolled substitutes, not mocks); no network, no
   filesystem, no subprocess — except the single designed goga-blocked facade-import subprocess check.
7. **Self-documenting test names; keep comments minimal.**
8. **Classification per the contract-oriented conventions**: contract tests (facade accessibility, API
   shape, signatures) written FIRST in each coding task and expected to fail; logic tests (positive,
   negative, edge) written AFTER implementation; integration tests as the final task. Integration tests
   never replace contract/logic tests.
9. **Traceability**: every test maps to a contract entity and a described requirement (the 16 scenarios
   below carry their design-verified setups, traces, and assertion literals — transfer them verbatim
   into the tests).
10. **Test dependencies** declared in `[project.optional-dependencies].test` (already true after Task 1).

### M3. Lint and Format Enforcement (across ALL development stages and local commits)

1. **ruff is the single linter and formatter**, configured in `pyproject.toml` (py310 target, 120 cols,
   full rule selection, `ignore = []` — zero warnings accepted; tests carry the declared per-file
   ignores). Do not add lint suppressions to make checks pass — fix the code.
2. **After every source or test file edit**, before moving on: run
   `/opt/project/bin/ruff format goga_tool_complex_build/ tests/` then
   `/opt/project/bin/ruff check goga_tool_complex_build/ tests/`.
3. **Every task ends with the LINT step** — a task is not complete while ruff reports anything.
4. **Local commits are gated**: immediately before every `git commit`, run the full gate —
   `ruff format --check` + `ruff check` + `pytest tests/ -x` all green (exact command in
   Validation Commands). If any gate step fails, fix the code (not the tests, not the contract) and
   re-run; never commit over a red gate.
5. Commits happen after each task passes its review/approval; commit only the task's deliverable files.

### M4. REPL Cycle Rules (continuous interactive evaluation, hot reloading, migration to source files)

The workflow is REPL-driven: the REPL is the continuous evaluation loop, source files are the only artifact.

1. **Probe before you pin**: before writing code or tests, exercise the real platform primitives in the
   `/opt/project` REPL (`/opt/project/bin/python`) — `HookRegistrar`, `ConfigAmendment`,
   `wrap_context`, `build_hook_arguments`, `merge_config_amendments`, `ConfigHooks` — and confirm the
   design-verified literals (guard message, four pairs, merge outcomes, summary lines) reproduce.
2. **Hot reloading**: keep one interactive session alive per task; after every edit to
   `registration.py`/`__init__.py` reload in place —
   `import goga_tool_complex_build.registration as r; importlib.reload(r)` (and re-import the facade) —
   then immediately re-evaluate behavior instead of restarting the interpreter.
3. **Continuous evaluation**: each task's REPL checkpoint (checkbox below) verifies the increment
   interactively against the design's expected values before and alongside the pytest run; every REPL
   probe that a test pins must match the design literals (design wins over ad-hoc observations).
4. **Migration to source files**: code that proved correct in the REPL is migrated verbatim into the
   source file (`registration.py`, `__init__.py`) — the file becomes the single source of truth. Nothing
   ships that lives only in a REPL session; no placeholder stays in a source file awaiting a REPL.
5. **REPL never replaces tests**: after migration, run the task's tests and the lint/format gate; the
   pytest suite and ruff, not the REPL, define done.
6. REPL sessions run inside `/opt/project` only; they never mutate the repo (no writes except through
   file edits), never touch the authored `.goga/config.yml`, and never print configuration values beyond
   the fixed test literals.

---

## Tasks

> **Package ordering rule**: coding tasks for each package are completed before starting the next. Within
> each coding task, contract tests are written first (TDD workflow). Only ONE task is executed per ralphex
> iteration.

### Task 1: Development environment and package scaffolding (infrastructure)

Context: prepare the `/opt/project` virtualenv (outside the project tree) with an editable install of
`goga_tool_complex_build` plus its test extra, extend `pyproject.toml` with the `goga>=2.0` test-only
requirement mandated by `goga_dependency`, and scaffold the test directory. No contract code is written
here — `registration.py` and the facade contents belong to Task 2. This task makes the platform primitives
available for the REPL cycle used throughout Tasks 2–3.

**Usages relevant to this task:**
- `goga_dependency`: `[project].dependencies` stays empty; goga appears exactly once — as `"goga>=2.0"`
  in `[project.optional-dependencies].test` (floor at the platform line, no upper cap).
- `conventions`: all commands in a virtualenv (create if missing); test libraries under the `test` extra.

**CRITICAL: `CODEMANIFEST` files — read-only contract definitions. Do NOT modify them. If implementation
does not match the contract, fix the implementation — never fix the contract. Also do NOT modify
`goga_tool_complex_build/.usages/comprehensive-review.md`.**

- [x] Create the venv outside the project: `python3 -m venv /opt/project` (skip creation if it already
  exists) and upgrade pip: `/opt/project/bin/pip install --upgrade pip`
  (adapted: `/opt` is root-owned and unwritable in this container — no sudo/docker; used the pre-existing
  writable venv at `/opt/goga` (the environment's own `python3`, already outside the project tree, "already
  exists → skip creation"); pip upgraded to 26.2.1 there; every `/opt/project/bin/...` command in Tasks 2–3
  maps to `/opt/goga/bin/...`)
- [x] Edit `pyproject.toml`: add `"goga>=2.0"` to `[project.optional-dependencies].test` (keep the list
  alphabetically ordered: `goga>=2.0`, `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-mock>=3.10`,
  `ruff>=0.15.0`); leave `[project].dependencies = []` and everything else untouched
- [x] Install editable with the test extra from the repository root (`/workspace`):
  `/opt/project/bin/pip install -e '.[test]'`
  (adapted: `/opt/goga/bin/python3 -m pip install -e '.[test]'` — installed goga-tool-complex-build
  0.1.dev3 editable + pytest 9.1.1, pytest-cov 7.1.0, pytest-mock 3.16.0, ruff 0.16.10; goga 2.0.2 already
  present satisfies `goga>=2.0`)
- [x] Create the test scaffold `tests/__init__.py` (empty file — every test directory MUST contain an
  `__init__.py`)
- [x] Verify install and platform availability:
  `/opt/project/bin/pip show goga-tool-complex-build` succeeds, and
  `/opt/project/bin/python -c "from goga.hooks.tools.registration import HookRegistrar; from goga.config.hooks.amendments import ConfigAmendment; import goga_tool_complex_build"` —
  the empty facade must already import cleanly (baseline; both platform names import from their real
  modules, NOT from the `goga.hooks`/`goga.config` facades)
  (verified via `/opt/goga/bin/...`: pip show succeeds; `HookRegistrar` from
  `goga.hooks.tools.registration`, `ConfigAmendment` from `goga.config.hooks.amendments`; the empty
  facade imports cleanly from `/workspace`)
- [x] **REPL checkpoint (M4)**: in `/opt/project/bin/python`, locate and import the delivery/merge
  primitives (`wrap_context`, `build_hook_arguments`, `merge_config_amendments`, `ConfigHooks`) plus the
  four config models (`ProjectConfig`, `BuildConfig`, `ReviewConfig`, `AdditionalReviewConfig`) from the
  goga modules where they live in the installed 2.0.2, and record the exact import paths for Tasks 2–3
  (verified here in goga 2.0.2: primitives in `goga.config.hooks.events`, models in `goga.config.project` —
  confirm interactively); confirm a fresh
  `HookRegistrar(tool="complex-build")` exposes `subscribe(...)` with no goga tool packages registered yet
  (confirmed in `/opt/goga/bin/python3`: `wrap_context`, `build_hook_arguments`,
  `merge_config_amendments`, `ConfigHooks`, `ToolAmendment` all import from `goga.config.hooks.events`;
  the four models from `goga.config.project` (dataclasses; `BuildConfig(review=…)`/`BuildConfig(agent=…)`
  valid); fresh `HookRegistrar(tool="complex-build")` exposes `subscribe`, `subscriptions == []`,
  `rejections == []`)
- [x] Lint: `/opt/project/bin/ruff check goga_tool_complex_build/ tests/` — must be clean (trivially true
  at this stage; establishes the gate)
- [x] Commit gate then commit (post-approval): gate command from Validation Commands green, then
  `git add pyproject.toml tests/__init__.py` and commit (message: `task 1: /opt/project venv, goga>=2.0 test extra, test scaffolding`)
  (gate: `ruff format --check` 3 files ok, `ruff check` all passed, `pytest tests/ -x` collected 0 items —
  exit 5 "no tests ran", the expected vacuous state at scaffolding since the suite arrives with Task 2's
  contract tests, zero failures/findings; commit message adapted to
  `task 1: dev venv (existing /opt/goga; /opt unwritable), goga>=2.0 test extra, test scaffolding`)

### Task 2: Implement `registration.py` (both Routines) and the facade re-export (TDD)

Context: the core coding task — both contract entities (`register_hooks`, `review_presets`, same
`location`, one task) plus the facade re-export they functionally require. Source files to create/modify:
`goga_tool_complex_build/registration.py` (new), `goga_tool_complex_build/__init__.py` (fill the empty
shell). Test files: `tests/conftest.py`, `tests/test_registration.py` (unit classes + contract-shape
test), `tests/test_init.py` (facade contract test). The full CODEMANIFEST algorithms, fixed literals, and
verified traces are in **Context → Contract Surface** above and are repeated per test below — implement
exactly those, nothing more.

**Usages relevant to this task:**
- `conventions`: coding style (M1) and test rules (M2) apply in full — relative imports, Google docstrings
  with `Args`/`Raises`, one-blank-line blocks, mandatory type hints, test mirroring/naming/fixtures.
- `hook_registration`: `register_hooks` performs exactly one
  `hooks.subscribe("config", "amend_config", "review_presets", review_presets)`; the hook declares only
  `context`, so the platform delivers exactly that by keyword; envelope problems are refused as data with
  a log warning, never raised.
- `config_amendment`: `review_presets` reads through `context.config` (attribute chain with `None`
  guards), contributes through `context.set(path, value)` only — `force` is never called; authored-wins
  is left to the merge layer; `None` is silence, `""`/`False` are authored.
- `goga_dependency`: `from __future__ import annotations` + `TYPE_CHECKING` block importing
  `HookRegistrar` from `goga.hooks.tools.registration` and `ConfigAmendment` from
  `goga.config.hooks.amendments`; no runtime goga import; no logging; no print.

**CRITICAL: `CODEMANIFEST` files — read-only contract definitions. Do NOT modify them. If implementation
does not match the contract, fix the implementation — never fix the contract.**

- [x] **Declaration**: declare task 2 in progress — implementing `register_hooks` + `review_presets` at
  `location: registration.py` and the facade re-export
  (declared in `.ralphex/progress/progress-plan.txt`, iteration "task iteration 2")
- [x] **Contract tests** (write first — expected to FAIL before implementation): create
  `tests/conftest.py` and `tests/test_init.py`, `tests/test_registration.py` with:
  - `tests/conftest.py` — shared fixtures per the design; platform imports verified in goga 2.0.2:
    `from goga.config.project import AdditionalReviewConfig, BuildConfig, ProjectConfig, ReviewConfig`
    (none of the four is exported by the `goga.config.hooks.*` modules) and
    `from goga.config.hooks.amendments import ConfigAmendment`:
    `project_config(build=…)` building a real `ProjectConfig(language="python", image=None,
    dockerfile=None, build=build, pipeline=None)`; `recording_view(request)` — a
    `_RecordingAmendment(ConfigAmendment)` subclass overriding `set`/`force` to append
    `(path, value)` / `("force", path, value)` records and delegate to `super()`, exposing
    `.set_calls`, `.force_calls`, and the real inherited buffer; `trap` — an object whose every attribute
    access raises `AssertionError`
  - `tests/test_init.py` `TestInit.test_facade_reexports_contract_api_by_identity`:
    `facade.__all__ == ["register_hooks", "review_presets"]`;
    `facade.register_hooks is registration.register_hooks`;
    `facade.review_presets is registration.review_presets`
  - `tests/test_registration.py` `TestContract.test_contract_routines_expose_declared_signatures`
    (conventions-mandated API-shape coverage): via `inspect.signature` — `register_hooks` has exactly the
    parameter `hooks`; `review_presets` has exactly the parameter `context`; both accept no variadics
  - Run `/opt/project/bin/python -m pytest tests/ -x` — the contract tests must FAIL at this stage
    (`ImportError`/`AttributeError`: the names do not exist yet)
    (verified via `/opt/goga/bin/python -m pytest tests/ -x`: ImportError "cannot import name
    'registration' from 'goga_tool_complex_build'" — exactly the expected red state before coding)
- [x] **Code**: create `goga_tool_complex_build/registration.py` — module docstring;
  `from __future__ import annotations`; `TYPE_CHECKING` block importing `HookRegistrar` from
  `goga.hooks.tools.registration` and `ConfigAmendment` from `goga.config.hooks.amendments`;
  **no runtime goga import; no logging; no print**; then:
  - `register_hooks(hooks: HookRegistrar) -> None` per its Algorithm (one `subscribe` call:
    domain `"config"`, action `"amend_config"`, name `"review_presets"`, hook `review_presets`);
    Google docstring with `Args`
  - `review_presets(context: ConfigAmendment) -> None` per its Algorithm: None-chain read of
    `build.review.strategy`; guard `if strategy is not None and strategy != "full"` raising
    `ValueError` with the EXACT fixed message
    `"authored value at build.review.strategy conflicts with the tool's purpose; remove the authored
    strategy or uninstall the tool"` (no interpolation, path only); then the four `context.set` calls in
    order: `("build.review.strategy", "full")`, `("build.review.max_iterations", 5)`,
    `("build.review.additional.patience", 2)`, `("build.review.additional.max_iterations", 3)`;
    Google docstring with `Args` and `Raises: ValueError`
- [x] **Code**: fill `goga_tool_complex_build/__init__.py` — module docstring;
  `from .registration import register_hooks, review_presets` (relative import, re-export by identity);
  `__all__ = ["register_hooks", "review_presets"]`; import-clean without goga
- [x] **Interface verification**: `/opt/project/bin/python -m pytest tests/test_init.py
  tests/test_registration.py::TestContract -v` — all contract tests pass
  (verified via `/opt/goga/bin/python -m pytest tests/test_init.py
  tests/test_registration.py::TestContract -v`: 2 passed)
- [x] **REPL checkpoint (M4)**: in the live `/opt/project` REPL, hot-reload after each edit
  (`importlib.reload`) and interactively confirm against a `recording_view`: silent config → exactly the
  four pairs in order; `strategy="short"` → the exact guard message and zero buffered sets;
  `strategy="full"` → still four sets (unconditional); `register_hooks(real HookRegistrar)` →
  1 subscription, 0 rejections — then let the migrated source files stand as the artifact
  (verified in `/opt/goga/bin/python -i` with `importlib.reload(registration)` + `importlib.reload(facade)`:
  silent → the four pairs in order, force_calls []; "short" → exact fixed message, zero sets; "full" →
  4 sets including strategy; real HookRegistrar(tool="complex-build") → 1 subscription, 0 rejections;
  facade identity re-export intact)
- [x] **Logic tests** (write after implementation, in `tests/test_registration.py`): the 10 unit-level
  design scenarios, with their design-verified setups and assertion literals:
  - `TestRegisterHooks.test_register_hooks_subscribes_single_hook_to_config_amend_config` —
    `_FakeRegistrar` recording `(domain, action, name, hook)`; assert `len(fake.calls) == 1`,
    `fake.calls[0][:3] == ("config", "amend_config", "review_presets")`,
    `fake.calls[0][3] is registration.review_presets` (by identity)
  - `TestRegisterHooks.test_register_hooks_envelope_accepted_by_real_registrar` — real
    `HookRegistrar(tool="complex-build")`; assert `len(registrar.subscriptions) == 1`,
    `[(s.domain, s.action, s.name) for s in registrar.subscriptions] ==
    [("config", "amend_config", "review_presets")]`, `registrar.rejections == []`
  - `TestReviewPresets.test_review_presets_buffers_four_presets_on_silent_config` —
    `project_config(build=None)`; assert exact list equality
    `view.set_calls == [("build.review.strategy", "full"), ("build.review.max_iterations", 5),
    ("build.review.additional.patience", 2), ("build.review.additional.max_iterations", 3)]` and
    `view.force_calls == []`
  - `TestReviewPresets.test_review_presets_with_authored_full_strategy_buffers_unconditionally` —
    `BuildConfig(review=ReviewConfig(strategy="full"))`; assert the same four exact pairs (the strategy
    `set` is buffered even when authored equals it — authored-wins is the merge layer's job)
  - `TestReviewPresets.test_review_presets_raises_value_error_on_conflicting_strategy_before_any_set` —
    `strategy="short"`; `pytest.raises(ValueError)`; assert `str(excinfo.value)` equals the fixed
    message, `"build.review.strategy" in str(excinfo.value)`, `view.set_calls == []`,
    `view.force_calls == []`
  - `TestReviewPresets.test_review_presets_error_message_never_contains_authored_value` —
    `strategy="s3cr3t-strategy-value"` sentinel; assert `"s3cr3t-strategy-value" not in
    str(excinfo.value)`, `"build.review.strategy" in str(excinfo.value)`, `view.set_calls == []`
  - `TestReviewPresets.test_review_presets_authored_empty_string_strategy_raises` — `strategy=""`
    (authored emptiness is authored, not silent); assert the fixed message and `view.set_calls == []`
  - `TestReviewPresets.test_review_presets_non_string_authored_strategy_raises` — `@pytest.mark.parametrize`
    over `5`, `True`, `1.5` (invalid-types boundary, per M2.5); assert the fixed message and
    `view.set_calls == []` for each
  - `TestReviewPresets.test_review_presets_absent_review_branch_with_present_build_section` —
    `BuildConfig(agent="claude")` (build present, review absent); assert the four exact pairs
  - `TestReviewPresets.test_review_presets_reads_strategy_chain_only` — unread branches planted with
    `trap` (`pipeline=trap`, `additional=None` etc. per the design setup); completing without tripping
    the traps and asserting the four exact pairs proves the read footprint
- [x] **Debugging**: `/opt/project/bin/python -m pytest tests/ -x` — fix implementation code until all
  tests pass (do NOT fix test code; do NOT touch the contract)
  (14 items passed on the first full run after implementation; the only fix needed was an import-path
  typo in the new test module itself — the implementation never changed after its first write)
- [x] **Contract re-verification**: facade importable and identity re-exports intact; signatures exactly
  `(hooks)` / `(context)`; guard message and four-pair footprint unchanged; no runtime goga import in
  either file (only `TYPE_CHECKING`)
  (verified in a fresh `/opt/goga/bin/python -c`: facade re-exports by identity, signatures `(hooks)` /
  `(context)`, `'goga' not in sys.modules` after import, and grep shows no module-level goga import)
- [x] **Lint**: `/opt/project/bin/ruff format goga_tool_complex_build/ tests/` then
  `/opt/project/bin/ruff check goga_tool_complex_build/ tests/` — zero findings; decompose if needed
  (final state: format "7 files left unchanged", check "All checks passed!"; the three initial findings —
  `collections.abc.Callable` imports, import order, PT011 broad ValueError — were fixed in the code, no
  suppressions added)
- [x] **Completion**: mark this task's checkboxes complete
- [x] Commit gate then commit (post-approval): gate green, then
  `git add goga_tool_complex_build/registration.py goga_tool_complex_build/__init__.py tests/conftest.py tests/test_registration.py tests/test_init.py`
  and commit (message: `task 2: register_hooks and review_presets routines, facade re-export, unit tests`)
  (gate via /opt/goga: ruff format --check 7 files ok, ruff check all passed, pytest tests/ -x 14 passed,
  facade import check OK; PT011 satisfied with match=re.escape(fixed message) alongside the exact
  equality assertions)

### Task 3: Integration tests through the real platform primitives (integration)

Context: the cross-boundary scenarios — the cell against the real goga mediation, merge, and checkpoint
machinery. No new production code is expected (any failure here is a Task 2 implementation defect or an
environment issue — fix the implementation, never the tests' design-verified literals). Test files:
extend `tests/test_registration.py` (`TestDelivery`, `TestCheckpointIntegration`) and
`tests/test_init.py` (subprocess check). Import the platform primitives from their verified modules —
`from goga.config.hooks.events import ConfigHooks, build_hook_arguments, merge_config_amendments,
wrap_context` (verified in goga 2.0.2; also re-confirm in Task 1's REPL checkpoint), `ToolAmendment`
likewise from `goga.config.hooks.events`.

**Usages relevant to this task:**
- `config_amendment`: merge semantics under test — authored-wins for `set`, absent-branch materialization,
  `AppliedAmendment` records, value-free summary lines; hard-action failure wrap naming hook/tool/action.
- `hook_registration`: the real registration path — enumeration discovers installed `goga_tool_*`
  packages by name, imports the facade, derives tool identity from the package name.
- `conventions` (M2): integration tests only for cross-package interaction; assertions carry exact
  design-verified literals; tool-name-filtered assertions keep the environment deterministic.
- `goga_dependency`: the package must import without goga installed — verified by the subprocess test.

**CRITICAL: `CODEMANIFEST` files — read-only contract definitions. Do NOT modify them.**

- [x] **Declaration**: declare task 3 in progress — integration tests for cell ↔ platform interaction
  (declared in `.ralphex/progress/progress-plan.txt`, iteration "task iteration 3", with the REPL findings
  and the one environment deviation recorded there)
- [x] **REPL checkpoint (M4)**: before writing the tests, reproduce the checkpoint interactively in the
  `/opt/project` REPL: `overlay = ConfigHooks().amend_config(config=ProjectConfig(language="python",
  image=None, dockerfile=None, build=None, pipeline=None))` — confirm the effective
  `full / 5 / 2 / 3`, the four `complex-build` applied records, the exact summary lines, and
  `config.build is None`; then migrate the verified expectations into the tests below
  (verified in `/opt/goga/bin/python`: delivery projection delivers only `context` by keyword; the silent-base
  merge yields effective `full/5/2/3`, the four `complex-build` records, the exact summary lines, and leaves
  `base.build is None`; the authored `full 5 4 0` base yields 2 applied paths; the goga-blocked subprocess
  returns 0. One environment deviation: the adapted shared venv `/opt/goga` also carries the platform's own
  `goga_tool_*` packages — `goga-tool-simple-build` contests 3 of the 4 preset paths and wins them
  (later-tool-wins), so a bare checkpoint yields `short/5/1/3`; the checkpoint test therefore pins the
  environment seam `goga.hooks.registry.state.enumerate_tool_packages` to the real enumeration filtered to
  `goga_tool_complex_build` — facade import, registration, delivery, and merge stay the real platform code;
  the foreign tools were NOT uninstalled, they serve this workspace's own platform runs)
- [x] **Code**: `TestDelivery.test_review_presets_through_real_delivery_projection` — recording view over
  `project_config(build=None)`; real `proxy = wrap_context(view)`; real
  `args = build_hook_arguments(review_presets, proxy, object())`; call `review_presets(**args)`; assert
  `sorted(args) == ["context"]`, the four exact `set_calls` pairs, and
  `[(a.path, a.intent, a.value) for a in view._amendments.values()] ==
  [("build.review.strategy", "set", "full"), ("build.review.max_iterations", "set", 5),
  ("build.review.additional.patience", "set", 2), ("build.review.additional.max_iterations", "set", 3)]`
- [x] **Code**: `TestDelivery.test_presets_merge_into_effective_review_config` — deliver into a real
  `ConfigAmendment` over silent `base`, build
  `ToolAmendment(tool="complex-build", amendments=list(view._amendments.values()))`, call real
  `merge_config_amendments(base, [contribution])`; assert
  `review.strategy == "full"`, `review.max_iterations == 5`, `review.additional.patience == 2`,
  `review.additional.max_iterations == 3`, `len(overlay.applied) == 4`,
  all records `tool == "complex-build"` and `intent == "set"`,
  `overlay.summary_lines == ["config amendments: 4 applied", "- complex-build set build.review.strategy",
  "- complex-build set build.review.max_iterations", "- complex-build set build.review.additional.patience",
  "- complex-build set build.review.additional.max_iterations"]`,
  and `base.build is None` (authored object untouched)
- [x] **Code**: `TestDelivery.test_presets_merge_honors_authored_wins_on_authored_leaves` — base with
  `ReviewConfig(strategy=None, additional=AdditionalReviewConfig(patience=4, max_iterations=0))`
  (authored `4` and authored zero); assert effective `strategy == "full"`, `max_iterations == 5`,
  `additional.patience == 4`, `additional.max_iterations == 0`, and
  `[r.path for r in overlay.applied] == ["build.review.strategy", "build.review.max_iterations"]`
  (authored leaves — including explicit zeros — win; the two corresponding sets are dropped)
- [x] **Code**: `TestInit.test_facade_imports_without_goga_installed` — subprocess
  (`sys.executable -c`, `cwd` at repository root) that installs `sys.modules["goga"] = None` (plus the
  known submodule keys) BEFORE importing `goga_tool_complex_build`, then prints `__all__` and the two
  callables; assert `result.returncode == 0` and both names appear in `result.stdout`
  (mechanism: `None` in `sys.modules` makes `import goga` raise `ImportError` — proves
  `from __future__ import annotations` + `TYPE_CHECKING` keep the facade goga-free at runtime;
  blocked keys: `goga`, `goga.config`, `goga.hooks`)
- [x] **Code**: `TestCheckpointIntegration.test_tool_amends_through_real_checkpoint` — the real
  orchestration: `overlay = ConfigHooks().amend_config(config=config)` with the package installed
  editable in the `/opt/project` venv; assert effective `full / 5 / 2 / 3`, the four
  `complex-build`-filtered applied records (`r.tool == "complex-build"`, `r.intent == "set"`),
  `"- complex-build set build.review.strategy" in overlay.summary_lines`, and
  `config.build is None` (tool-name-filtered assertions keep foreign `goga_tool_*` packages from
  breaking the test; additionally — see the REPL note — the enumeration seam is pinned to
  `goga_tool_complex_build` because in the shared `/opt/goga` venv `goga-tool-simple-build` would
  otherwise win the contested paths, and winner-take-all merge drops the `complex-build` records
  entirely, not just the effective values)
- [x] **Run validation**: `/opt/project/bin/python -m pytest tests/ -x` — the full suite
  (all 16 design scenarios + the contract-shape test) passes; facade check
  `/opt/project/bin/python -c "from goga_tool_complex_build import register_hooks, review_presets"`
  succeeds in a plain interpreter
  (verified via `/opt/goga/bin/...`: 19 items passed in 0.07s — exactly the parametrized expansion; facade
  check OK)
- [x] **Lint**: `/opt/project/bin/ruff format goga_tool_complex_build/ tests/` then
  `/opt/project/bin/ruff check goga_tool_complex_build/ tests/` — zero findings
  (final state: format "7 files left unchanged", check "All checks passed!"; the single finding — PLW1510
  `subprocess.run` without explicit `check` — was fixed in the code with `check=False`, no suppressions)
- [x] **Completion**: mark this task's checkboxes complete
- [x] Commit gate then commit (post-approval): gate green, then
  `git add tests/test_registration.py tests/test_init.py` and commit
  (message: `task 3: delivery, merge, and real-checkpoint integration tests`)
  (gate via /opt/goga: ruff format --check 7 files ok, ruff check all passed, pytest tests/ -x 19 passed;
  plan update committed together with the tests)

---

## Validation Commands

All commands run from the repository root (`/workspace`) with the `/opt/project` venv (M1.2).

- `/opt/project/bin/python -m pytest tests/ -x`: Run all tests (the full suite — 16 design scenarios +
  the contract-shape test; parametrization expands to 19 test items)
- `/opt/project/bin/python -m pytest tests/test_registration.py -v`: Run a specific module's tests
- `/opt/project/bin/ruff check goga_tool_complex_build/ tests/`: Lint check (zero findings — `ignore = []`)
- `/opt/project/bin/ruff format --check goga_tool_complex_build/ tests/`: Formatter check (double quotes,
  120 cols, LF)
- `/opt/project/bin/python -c "from goga_tool_complex_build import register_hooks, review_presets"`:
  Facade accessibility in a plain interpreter (no goga import needed)
- **Pre-commit gate (M3.4 — run immediately before EVERY local commit, must be fully green):**
  `/opt/project/bin/ruff format --check goga_tool_complex_build/ tests/ && /opt/project/bin/ruff check goga_tool_complex_build/ tests/ && /opt/project/bin/python -m pytest tests/ -x`

---

## Completion Criteria

- [x] Every contract entity is implemented in the correct `location` (`registration.py` — both Routines)
- [x] Every contract entity is accessible from the facade (`__all__ = ["register_hooks", "review_presets"]`,
      re-exported by identity)
- [x] Properties and methods match the declared API (signatures exactly `(hooks: HookRegistrar)` /
      `(context: ConfigAmendment)` → `None`; type hints mandatory)
- [x] Descriptions are reflected in behavior (the fixed guard message; the four `set` pairs in the fixed
      order; guard strictly before any buffering; unconditional amendments; read footprint limited to the
      strategy chain; `force` never called)
- [x] Contract dependencies are met (`goga>=2.0` test-only; no runtime goga import; `TYPE_CHECKING` only)
- [x] Re-exports are accessible from the facade
- [x] Every coding task followed the TDD workflow (contract tests → code → verification → logic tests →
      debugging → re-verification → lint)
- [x] Contract tests and logic tests cover facade, API, and behavior within each coding task
- [x] Integration tests exist where cross-entity scenarios require them (Task 3 — real delivery, merge,
      and checkpoint)
- [x] No package boundary was expanded (no new cells, no new interfaces beyond the contract)
- [x] `CODEMANIFEST` files were not modified (contract is read-only);
      `goga_tool_complex_build/.usages/comprehensive-review.md` untouched
- [x] All validation commands pass (tests, lint, format check, facade check)
- [x] Every Usages entry is mentioned in at least one task (`conventions`, `hook_registration`,
      `config_amendment`, `goga_dependency`)
- [x] Mandatory rules M1–M4 were followed throughout: coding style per `conventions`, test writing per
      `conventions`, ruff lint + format enforced after every edit / at every task end / before every local
      commit, and the REPL cycle (probe → hot-reload → evaluate → migrate to source files → re-verify)
      drove development in Tasks 1–3
- [x] Local commits exist only behind a green pre-commit gate, one commit per completed task
