# complex-build — hook-only comprehensive-review preset tool package

## Current State

The repository is a scaffold for the `goga-tool-complex-build` package:

- `pyproject.toml` is ready (setuptools + setuptools-scm, ruff, pytest, Python >= 3.10, runtime `dependencies = []`); the `test` extra lacks the `goga>=2.0` entry the dependency policy requires.
- `goga_tool_complex_build/` contains only an empty `__init__.py` — no registration module, no CODEMANIFEST, no `.usages/` practices.
- No `tests/` directory exists.
- `goga schema` is empty — the project has no cells and no architecture yet.
- Project practices: `conventions` (`.goga/usages/conventions.md`) and the base annotation; the synced platform usages `github/goga` are available locally and are authoritative for this task — no clones of and no network interaction with the usages repository: work strictly from the local synced state (verified during discovery).
- The precedent package `goga-tool-simple-build` (installed at `/opt/goga/...`, source at `qarium/goga-tool-simple-build`, branch `master`) fully defines the target shape: facade `__init__.py`, `registration.py` with `register_hooks` plus the hook routine, `CODEMANIFEST`, `.usages/review-presets.md`, and the four-file test suite.

## Description

Implement the `complex-build` goga tool package: a hook-only config-amendment preset tool that gives every build of an adopting project a comprehensive review. The package subscribes exactly once — the hook `review_presets` to the hard `config / amend_config` action — and contributes four unconditional apply-where-silent (`set`) amendments wherever the authored configuration is silent:

```yaml
build:
  review:
    strategy: full
    max_iterations: 5
    additional:
      patience: 2
      max_iterations: 3
```

The hook reads exactly one configuration leaf — the guard `build.review.strategy`. When the authored strategy is present and is not `full`, the hook raises; the hard action turns that into the single clean tool-named error that stops the command before anything launches and discards the whole contribution. Authored-wins (explicit zeros included) is owned by the platform merge — the tool never re-derives it. There is no CLI, no runtime import of goga, and no tool-side printing: the amendment summary on stderr is platform-owned.

## Scope

**In scope:**

- `goga_tool_complex_build/registration.py`: `register_hooks(hooks)` subscribing `review_presets` to `config / amend_config`; the hook routine `review_presets(context)` performing the guard read and buffering the four `set` amendments.
- `goga_tool_complex_build/__init__.py`: facade re-exporting `register_hooks` and `review_presets` by identity through `__all__`; import-clean with or without goga installed.
- `goga_tool_complex_build/CODEMANIFEST`: the cell contract mirroring the precedent's structure (header `Usages`: `conventions`, `config_amendment`, `hook_registration`, `goga_dependency`; the two routine declarations; footer). Final cell boundaries and manifest wording are formalized by the following architecture stage.
- `goga_tool_complex_build/.usages/comprehensive-review.md`: maintainer-facing practice, analog-style (`review-presets.md` of the precedent).
- `tests/` — four files following the precedent's architecture:
  - `tests/__init__.py` — package marker required by `conventions` (Test Structure rule 1).
  - `tests/test_registration.py` — unit tests on stand-in fakes (`StandinRegistrar`, `StandinAmendment`, authored-tree stand-ins, `RecordingLevel` for read-footprint assertions): single subscription envelope; the four buffered presets; guard raise for any authored strategy other than `full` (including `""`) naming the path and never the value, with an empty buffer; absent intermediate branches read as absent; authored `full` still buffers all four; read footprint is the `build.review.strategy` chain only.
  - `tests/test_init.py` — facade re-export by identity, exact `__all__`, and import in a fresh interpreter without loading any goga module.
  - `tests/test_integration.py` — real `python -m goga config` in a throwaway project (`skipif` goga absent): presets applied on a minimal config with the amendment summary naming `complex-build`; authored values win per path with the non-silent `set` silently dropped from the summary; strategy conflict stops the command with the tool-named error leaking no value; authored file stays byte-identical.
  - `tests/test_pyproject.py` — dependency policy guard: runtime `dependencies = []`, exactly one `goga>=` requirement, inside the test extra only.
- `pyproject.toml`: add `goga>=2.0` as the first entry of the `test` extra.
- Local installability: `goga install --local .:complex-build`.

**Out of scope** (per PRD and ADR):

- A CLI entry point (`goga tool complex-build ...`).
- Configurability of the preset values.
- Iteration-cap remapping and the both-caps conflict guard (the `simple-build`-style behavior); both caps are independent authored-wins knobs here.
- Detection or handling of coexistence with other config-amending tools.
- Any change to the goga platform and to this repository's own `.goga/config.yml` (the repository stays on `simple-build`).
- User-facing documentation beyond the scaffold (docs site).
- Release publishing.

## Acceptance Criteria

- With the tool enabled over a silent authored configuration, the effective review configuration is `strategy: full`, `max_iterations: 5`, `additional.patience: 2`, `additional.max_iterations: 3`; the stderr amendment summary names `complex-build` with four `set` lines; `goga config` shows the effective values.
- Authored values (explicit zeros included) win at their paths independently; the tool fills only silent leaves; the authored file is never modified.
- An authored `build.review.strategy` other than `full` stops every config-consuming command at load with a single clean error naming `complex-build` and the path, before anything launches; deterministic; authored `full` or an absent strategy triggers no error.
- The effective configuration equals the authored one everywhere except the four review knobs.
- `pytest tests/ -x` passes; `ruff check goga_tool_complex_build/` is clean; the facade imports in a fresh interpreter without goga.
- `goga install --local .:complex-build` succeeds.

## Stack

- **Language:** Python >= 3.10, runtime stdlib only.
- **Frameworks:** none — plain package conforming to the goga tool-package facade contract (goga 2.0.x).
- **Libraries:** none at runtime. Test/lint: `goga>=2.0`, `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-mock>=3.10`, `ruff>=0.15.0` (test extra).
- **Infrastructure:** none. Packaging: setuptools + setuptools-scm; local install via `goga install --local .:complex-build`.

## External Dependencies

| Component | Usage file | Status |
|-----------|------------|--------|
| Code and test conventions | `.goga/usages/conventions.md` | existing (project) |
| goga dependency policy | `.goga/usages/cooks/goga-dependency.md` | created (verbatim from the precedent) |
| Config amendment contract (view, silence, merge) | `.goga/usages/github/goga/config/registering-hooks.md` | existing (synced) |
| Hook registration (facade callback, subscribe) | `.goga/usages/github/goga/hooks/registering-hooks.md` | existing (synced) |

Synced usage files are managed by `goga usages sync` — reference them read-only, never create or update them in the task.

## Risks and Constraints

- The amendment contract is hard: a raising hook stops the whole command and discards the tool's contribution — the guard must raise before any `set` is buffered (asserted by tests).
- Value-free feedback: no configuration value may appear in any tool output or error message; messages name paths only.
- No runtime import of goga; platform types under `TYPE_CHECKING` only — a broken facade import is fatal to every goga command.
- No clones of and no network interaction with the usages repository — the local synced usages `github/goga` are the sole reference; integration tests run against the locally installed goga 2.0.2.
- Coexistence with other config-amending tools is platform-governed; the tool neither detects nor vetoes neighbors.

## Scope Estimate

Single task — no decomposition. Two contract routines in one module plus a facade, one cell (the package itself); the scope is smaller than the precedent (no cap mapping, no second conflict guard).

## Existing Architecture

No cells exist (`goga schema` is empty). The architecture stage following this task defines the cell layout and the CODEMANIFEST contract of the package, guided by the precedent `goga-tool-simple-build`. Integration requirement: the facade callback name `register_hooks` is fixed by the platform discovery; tool identity `complex-build` is assigned by the platform from the package name.

## Notes

- Decisions inherited from the ADR (`.goga/history/2026/the-first-version/adr.md`): hook-only shape, single hard subscription under the hook name `review_presets`, four unconditional `set` contributions, guard on the strategy leaf only, `force` forbidden, tests on fakes, maintainer `.usages` doc shipped.
- ADR unresolved questions resolved by this task: facade composition (re-export `register_hooks` and `review_presets`), test architecture (the precedent's four files), guard message wording (precedent-adapted, below). Cell boundaries and CODEMANIFEST wording remain with the architecture stage.
- Proposed guard message, adapted from the precedent (value-free, path-naming): `"authored value at build.review.strategy conflicts with the tool's purpose; remove the authored strategy or uninstall the tool"`.
- Target API, precedent-adapted (orientation for the architecture stage; the precedent is the normative example):

```python
# goga_tool_complex_build/__init__.py
"""Facade of the complex-build tool: the contract API re-exported by identity."""

from .registration import register_hooks, review_presets

__all__ = ["register_hooks", "review_presets"]
```

```python
# goga_tool_complex_build/registration.py
"""Hook registration of the complex-build tool: the review-presets config hook."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goga.config.hooks.amendments import ConfigAmendment
    from goga.hooks.tools.registration import HookRegistrar

_STRATEGY_CONFLICT_MESSAGE = (
    "authored value at build.review.strategy conflicts with the tool's purpose; "
    "remove the authored strategy or uninstall the tool"
)


def register_hooks(hooks: HookRegistrar):
    """Subscribe the tool's single review-presets hook to the configuration amendment action.

    Args:
        hooks: platform registration surface delivered to the facade callback.
    """
    hooks.subscribe("config", "amend_config", "review_presets", review_presets)


def review_presets(context: ConfigAmendment):
    """Contribute the four comprehensive-review presets and guard the authored strategy.

    Args:
        context: read-and-amend view over the authored configuration.

    Raises:
        ValueError: the authored value at build.review.strategy conflicts with the tool's purpose.
    """
    build = context.config.build

    review = build.review if build is not None else None
    strategy = review.strategy if review is not None else None

    if strategy is not None and strategy != "full":
        raise ValueError(_STRATEGY_CONFLICT_MESSAGE)

    context.set("build.review.strategy", "full")
    context.set("build.review.max_iterations", 5)
    context.set("build.review.additional.patience", 2)
    context.set("build.review.additional.max_iterations", 3)
```

```python
# tests/test_registration.py — mini-example of the stand-in pattern
def test_review_presets_buffers_four_presets_when_branches_absent():
    """Buffers the four exact presets when no build branch exists at all."""
    amendment = StandinAmendment(config=StandinConfig(build=None))

    result = registration.review_presets(context=amendment)

    assert result is None
    assert amendment.buffered == [
        ("build.review.strategy", "full"),
        ("build.review.max_iterations", 5),
        ("build.review.additional.patience", 2),
        ("build.review.additional.max_iterations", 3),
    ]
```
