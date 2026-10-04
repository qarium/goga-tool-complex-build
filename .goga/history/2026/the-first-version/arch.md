# Architecture Plan — complex-build review-presets tool

## Topic

**Short name:** complex-build — comprehensive-review preset tool (hook-only config-amendment package)
**Plan path:** `.goga/history/2026/the-first-version/arch.md` (topic: `.goga/history/2026/the-first-version`)
**Project schema before this plan:** empty (`goga schema` → `[]`) — this plan creates the project's first cell.

## Implementation Order

1. **`goga_tool_complex_build`** — created anew. First and only cell; it has no `Imports` (no dependencies on other
   project cells), so it is both leaf and root. The only external relationship is the goga platform itself at runtime
   (fixed facade callback name `register_hooks`; tool identity `complex-build` assigned from the package name).

## Artifacts

### Cell: `goga_tool_complex_build` (created anew)

Cell structure (Python package):

```
goga_tool_complex_build/
├── CODEMANIFEST
├── __init__.py          # facade: re-export of the contract API through __all__
├── registration.py      # location of both routines
└── .usages/
    └── comprehensive-review.md
```

#### Artifact 1 — CODEMANIFEST

**Path:** `goga_tool_complex_build/CODEMANIFEST` — **create**

```yaml
Usages:
  conventions: .goga/usages/conventions.md
  config_amendment: .goga/usages/github/goga/config/registering-hooks.md
  hook_registration: .goga/usages/github/goga/hooks/registering-hooks.md
  goga_dependency: .goga/usages/cooks/goga-dependency.md

Annotations: |
  Use `conventions` for code writing rules and testing.
  Use `hook_registration` from Usages for the facade callback and subscription contract.
  Use `config_amendment` from Usages for the amendment view, silence markers, and merge semantics.
  Use `goga_dependency` from Usages for the goga dependency policy.

  The cell is hook-only: no CLI facade and no runtime import of goga — platform types
  (HookRegistrar, ConfigAmendment) are referenced under TYPE_CHECKING only, and the
  package facade stays import-clean with or without goga installed.
  The package facade re-exports the contract API through __all__.
  Contribute amendments exclusively through the apply-where-silent form; never the override form.

---

"register_hooks(hooks: HookRegistrar)":
  location: registration.py
  annotations: |
    Subscribe the tool's single review-presets hook to the configuration amendment action.

    `hooks`: platform registration surface delivered to the facade callback

    Algorithm:
    1. Subscribe `review_presets` to the config / amend_config address under the hook
       name review_presets, using the subscribe operation of `hooks` defined in `hook_registration`

    Requirements:
    - Hook name stays unique per tool per address

    Constraints:
    - Subscribe to no other domain action
    - Do not validate any configuration leaf

"review_presets(context: ConfigAmendment)":
  location: registration.py
  annotations: |
    Contribute the four comprehensive-review presets and guard the authored strategy.

    `context`: read-and-amend view over the authored configuration, delivered per `config_amendment`

    Algorithm:
    1. Read the authored leaf build.review.strategy from the configuration of `context`;
       absent branches read as absent
    2. If the authored value is present and is not full — raise ValueError whose message
       names the path build.review.strategy and never the authored value
    3. Buffer four apply-where-silent amendments through `context`: build.review.strategy
       set to full, build.review.max_iterations set to 5,
       build.review.additional.patience set to 2, build.review.additional.max_iterations
       set to 3

    Requirements:
    - The guard raise of step 2 happens before any amendment is buffered
    - The guard message is the fixed strategy-conflict message: authored value at
      build.review.strategy conflicts with the tool's purpose; remove the authored
      strategy or uninstall the tool
    - Amendments are unconditional — the deliberate reads of the configuration are the
      guard leaf of step 1 only
    - Authored-wins is owned by the merge layer — never re-derived here
    - The exact write footprint is the four leaf paths of step 3 and nothing else

    Constraints:
    - Never use the override form of amendment — the presets never overwrite authored values
    - Never print or embed configuration values in any output or error message
    - Do not validate any leaf beyond the strategy guard

---

Author: Goga
CreatedAt: 04/10/26
Description: |
  Review presets for comprehensive builds: the tool's single subscription to the goga
  configuration amendment action, contributing the four review leaves — the full
  strategy, the review-level iteration cap, and the two external review knobs — and
  guarding the strategy conflict.
```

#### Artifact 2 — cell usage file

**Path:** `goga_tool_complex_build/.usages/comprehensive-review.md` — **create**

```md
# Comprehensive review — what an installed tool guarantees

For project maintainers who install `goga-tool-complex-build` into a goga project
and want every build to run a comprehensive review. The tool is hook-only: there
is no command to run and no file to edit for its part — the presets apply from
the first config-consuming goga run after installation.

## What you get

With the tool installed, every goga run that loads `.goga/config.yml` receives
four review presets wherever the authored configuration is silent:

| Path | Value |
|---|---|
| `build.review.strategy` | `full` |
| `build.review.max_iterations` | `5` |
| `build.review.additional.patience` | `2` |
| `build.review.additional.max_iterations` | `3` |

Absent intermediate branches (`build.review`, `build.review.additional`)
materialize on their own — a minimal configuration of `language` alone is enough.

## Relying on the effective values

A minimal authored configuration:

```yaml
language: python
```

Effective review configuration in every run:

```yaml
build:
  review:
    strategy: full
    max_iterations: 5
    additional:
      patience: 2
      max_iterations: 3
```

Check the effective values after a run with `goga config` — it prints the amended
values; the run also prints a short amendment summary to stderr naming the tool
and each applied path.

## Authoring your own values

Any review knob written explicitly wins. Author `patience`, `max_iterations`, or
`build.review.additional.max_iterations` (or `strategy: full`) and the tool stays
silent for those leaves — no warning, no error — while the remaining silent leaves
still receive their presets. Explicit zeros are authored, not silent — they win
like any other authored value:

```yaml
build:
  review:
    additional:
      patience: 4   # authored — wins over the preset 2
      max_iterations: 0   # authored zero — wins over the preset 3
```

Effective: `strategy: full`, `max_iterations: 5`, `patience: 4`,
`additional.max_iterations: 0`.

The two iteration caps are independent knobs: `build.review.max_iterations` and
`build.review.additional.max_iterations` only receive their presets when silent
and never interact — author either, both, or neither.

## The deliberate conflict

Authoring `build.review.strategy` with a value other than `full` conflicts with
the tool's purpose. Every config-consuming goga command stops with a clean error
naming the tool, the action, and the path `build.review.strategy` — the authored
value is never printed, nothing is applied. Remove the authored strategy or
uninstall the tool to resolve it.

```yaml
build:
  review:
    strategy: short   # conflict — every goga command stops
```

## Side effects and reversibility

- The authored `.goga/config.yml` is never modified — it stays byte-identical;
  the presets live only in the effective in-memory configuration of each run.
- Repeated runs reproduce the same effective configuration.
- Removing the tool from the environment returns the project to exactly its
  authored behavior.
- The tool never validates agent presence and never touches agent values — a
  configuration with no review agent loads without any error from the tool.
```

## Dependency Map

No inter-cell `Imports` — the project graph is a single node:

```
                    [goga platform]  (runtime delivery, not a project cell)
                          ▲
        register_hooks(hooks) │ review_presets(context)
        subscribe("config","amend_config","review_presets",…) │ set(path, value) ×4
                          │
        +-----------------------------------------+
        | goga_tool_complex_build                 |  Imports: none
        |   register_hooks  ·  review_presets     |  Cycles: none
        +-----------------------------------------+
```

## Verification Checklist

After materializing the plan (cell creation):

- [ ] `goga schema` lists the cell `goga_tool_complex_build` with types `register_hooks`, `review_presets` and usage
      `comprehensive-review`
- [ ] `goga lint` reports no DSL errors for `goga_tool_complex_build/CODEMANIFEST`
- [ ] The facade `goga_tool_complex_build/__init__.py` re-exports `register_hooks` and `review_presets` by identity
      through `__all__`, importable in a fresh interpreter without goga installed
- [ ] `review_presets` raises ValueError (fixed value-free message naming `build.review.strategy`) **before** any
      `set` is buffered when the authored strategy is present and ≠ `full`; with authored `full` or absent strategy
      all four `set` amendments are buffered: `build.review.strategy=full`,
      `build.review.max_iterations=5`, `build.review.additional.patience=2`,
      `build.review.additional.max_iterations=3`
- [ ] Read footprint is the `build.review.strategy` chain only; write footprint is exactly the four leaf paths
- [ ] `pytest tests/ -x` passes; `ruff check goga_tool_complex_build/` is clean
- [ ] The dependency policy holds: runtime `dependencies` stays empty and exactly one
      `goga>=2.0` requirement exists, inside the `test` extra only
- [ ] With the tool installed over a silent config, `goga config` shows the effective values and the stderr summary
      names `complex-build` with four `set` lines; authored file stays byte-identical
- [ ] `goga install --local .:complex-build` succeeds
