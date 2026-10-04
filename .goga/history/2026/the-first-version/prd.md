# Complex Build — Comprehensive Review Preset Tool for goga

## Problem

Maintainers of goga-based projects want every build to pass a comprehensive review — internal plus external reviewers with bounded iteration loops — but goga's default review configuration is the medium strategy: external review disabled, no iteration caps. The desired combination — a full-strategy review with bounded review iterations and bounded external-review patience — must be hand-written in each project's `.goga/config.yml`.

Across the several projects of an organization, this manual repetition produces inconsistent review setups: forgotten caps lead to unbounded and expensive review loops, and missing or wrong strategy settings silently weaken the review. No reusable preset exists for the "complex build" direction — the existing `simple-build` tool covers only the opposite, "short" direction.

## Users

**Primary — goga project maintainer.** Owns a project's `.goga/config.yml`; the organization runs several goga projects. Wants to give every build of a project a comprehensive, consistently configured review without hand-writing review knobs in each project. Expects that:

- enabling the tool is a one-time, declarative step with no per-run actions;
- authored review settings keep winning wherever the tool only fills gaps;
- contradictions with the tool's purpose surface as a clear error naming the tool, never as silent behavior.

**Secondary — build runner.** A developer or CI invoking `goga build` in a project where the tool is enabled. Wants to run the build and trust that the review cycle is the thorough, bounded one. Expects no new commands or flags; when the project configuration contradicts the tool, the run stops early with a clean error instead of a silently weakened review.

## Goals

1. **One declarative adoption step.** A maintainer enables the comprehensive-review build setup once, and every `goga build` of that project runs a thorough review cycle — internal plus external review — with bounded iteration loops, without hand-writing review knobs.
2. **Consistent comprehensive review across adopting projects.** The same review strategy, iteration caps, and external-review patience apply wherever the tool is enabled — no configuration drift, no accidentally weakened review.
3. **Authored control preserved.** Values a maintainer deliberately sets for the review iteration caps and the external-review patience win over the tool's defaults, so tuning a project stays in the authored configuration.
4. **Fail-loud configuration.** An authored review strategy that contradicts the comprehensive-review intent stops the command with a clear error naming the tool, instead of silently producing a weaker review.

## User Experience

### Entry point

A project maintainer enables the complex-build tool in their goga project — a one-time, declarative adoption through the project's tool setup, the same way existing goga tools are adopted. From that moment the tool participates in every configuration-consuming goga command of the project.

### Primary scenario

The maintainer runs any goga command (for example `goga build`) while the authored `.goga/config.yml` is silent about the review knobs:

- the effective configuration gains the comprehensive-review values: review strategy `full` (internal plus external review), review iteration cap `5`, external-review patience `2`, external iteration cap `3`;
- the command prints a short amendment summary on stderr identifying the tool and the applied paths — configuration values are never printed, and stdout stays data-clean;
- `goga build` then runs its usual two-pass cycle, unchanged in structure: the review pass is the full one — internal reviewers plus external review — bounded by the effective iteration caps, with the external review stopping early after the effective patience count of consecutive unchanged rounds;
- everything else about the build flow stays exactly as before.

### Alternative scenario: authored tuning

The maintainer deliberately sets review iteration caps or external-review patience in the authored configuration. Their values win over the tool's defaults; the tool fills only the knobs the authored configuration leaves silent. The build visibly uses the authored values, and the authored file is never modified.

### Failure scenario: contradictory strategy

The authored configuration sets `build.review.strategy` to a value other than `full` (for example `medium` or `short`):

- the goga command being run stops immediately with a single clean error naming the tool and the reason — the value contradicts the tool's purpose;
- nothing launches: no build passes run, no build events fire;
- the authored file is left untouched;
- recovery: the maintainer removes or aligns the authored strategy, or stops using the tool; the next run succeeds. Retrying without a fix reproduces the same error deterministically.

### States

- **Not enabled** — default review behavior (medium strategy, no caps).
- **Enabled, compatible** — the comprehensive review is in effect on every run.
- **Enabled, contradictory strategy** — every configuration-consuming command fails at configuration load until the conflict is removed.

### Feedback

- Applied contributions are reported in the amendment summary on stderr (tool, path, kind); configuration values are never printed.
- A contradictory authored strategy produces a single clean error naming the tool.
- `goga config` shows the effective (amended) values, so the maintainer can verify what is in effect.

### Consequences and recovery

The authored configuration file is never modified and remains the source of truth. Disabling the tool reverts the project to its authored-only configuration. Behavior is deterministic: the same authored file and the same enabled tool set always produce the same effective configuration.

## Requirements

### Preset contribution

When the tool is enabled and the authored project configuration is silent at a review knob, the effective configuration must provide:

```yaml
build:
  review:
    strategy: full
    max_iterations: 5
    additional:
      patience: 2
      max_iterations: 3
```

### Authored values win

- Authored values at `build.review.max_iterations`, `build.review.additional.max_iterations`, and `build.review.additional.patience` must win over the tool's defaults, each path independently. Both iteration caps may be authored simultaneously; this is not a conflict, and no error is raised for it.
- Authored explicit values count as authored even when they are zero or empty — patience `0` means disabled, an external cap `0` means the platform's automatic behavior — and the tool must not replace them.

### Strategy guard

When the authored `build.review.strategy` holds any value other than `full`, every goga command that loads the project configuration must stop with a single clean error naming the tool and the reason, before any pass or pipeline launches. The authored file must remain byte-identical. The failure must repeat deterministically until the conflict is removed. An authored `full`, or an absent strategy, is compatible and triggers no error.

### Effective build behavior

Under the effective configuration, the review pass of `goga build` must run the full strategy — internal review with the external review enabled — bounded by the effective iteration caps, with the external review stopping early after the effective patience count of consecutive unchanged rounds.

### Feedback

- Applied contributions must be reported in the amendment summary on stderr (tool, path, kind of contribution) with no configuration values printed; stdout must stay data-clean.
- `goga config` must show the effective (amended) values.

### Non-destructiveness and determinism

- The tool must never modify the authored configuration file.
- Disabling the tool must revert the project to its authored-only behavior.
- The same authored file and the same enabled tool set must always produce the same effective configuration.

### Scope of effect

The tool's contributions must be limited to the four review knobs above. Agents, environment layers, `base_ref`, reviewer roles, finalize settings, tasks-pass settings, and every other part of the configuration must pass through unchanged.

## Constraints

- **Platform extension boundary.** goga is extended only through the published tool-package surface; the product is a distributable goga tool package, with no changes to goga's own code.
- **Configuration amendment contract.** Contributions obey goga's config amendment contract: authored-wins semantics for gap-filling contributions; a failing tool stops the command as a hard action — its whole contribution is discarded and a clean error names the tool and the action; a tool can inspect only the authored configuration, never other tools' contributions (tools are mutually blind).
- **Platform-owned strategy semantics.** The meaning of `full`, `medium`, and `short` is owned by goga build; the tool selects and guards the authored strategy value but cannot redefine what a strategy does.
- **Authored configuration immutability.** The authored `.goga/config.yml` is never rewritten; only effective in-memory amendments exist.
- **Fixed identity.** The tool's identity is fixed by its package name — `complex-build` (`goga_tool_complex_build`); user-facing errors and the amendment summary name it accordingly.
- **Platform version.** The tool targets the goga 2.0.x configuration vocabulary and hook contract — the platform surface this repository consumes.
- **Secret-safe output.** goga never prints configuration values; the tool's feedback must stay value-free (paths and contribution kinds only).
- **Coexistence is platform-governed.** Interaction with other configuration-amending tools (for example `simple-build`) is governed by the platform merge rules — per-path precedence, the later tool in enumeration order winning among equal intents; the tool cannot detect or veto another tool.

## Scope

### In Scope

- The complex-build tool package: the four-knob comprehensive-review preset contribution with authored-wins semantics (`strategy: full`, review `max_iterations: 5`, `additional.patience: 2`, `additional.max_iterations: 3`).
- The strategy guard: an authored strategy other than `full` produces a clean, tool-named error that stops the command at configuration load.
- Distribution as an installable goga tool package that complies with the tool-package facade contract, so goga discovers and delivers its contribution.

### Out of Scope

- Any change to this repository's own `.goga/config.yml` — the repository is only the package's home and stays on `simple-build`.
- Any change to the goga platform: strategy semantics, the amendment contract, the merge rules.
- Iteration-cap remapping or a both-caps conflict guard (the `simple-build`-style behavior); under this tool both caps are independent authored-wins knobs.
- A CLI entry point for the tool (`goga tool complex-build …`).
- Configurability of the preset values (a tool-level configuration overriding the preset).
- Detection or handling of coexistence with other configuration tools.
- Contributions to any other configuration: tasks-pass settings, environment layers, reviewer roles, finalize, `base_ref`, and the rest.
- User-facing documentation beyond the scaffold (the docs site); usages files are not counted as documentation for this change.
- Organization-wide rollout of the tool to other projects.

## Success Criteria

1. **Preset applies.** In a project where the tool is enabled and the authored configuration is silent about the review knobs, the effective review configuration holds `strategy: full`, review iteration cap `5`, external patience `2`, external iteration cap `3`; the amendment summary on stderr names `complex-build`; `goga config` shows the effective values.
2. **Deterministic and consistent.** Repeated runs — and different projects with silent authored review knobs — produce the identical effective review configuration; the authored file is never modified.
3. **Authored values win.** Authored iteration caps or patience (including explicit zeros) prevail at their paths; the tool fills only the silent knobs.
4. **Guard works.** With an authored strategy other than `full`, every configuration-consuming goga command stops with a single clean error naming `complex-build` before anything launches; the failure is deterministic; removing the conflict restores normal operation.
5. **Effective build behavior.** The review pass of `goga build` runs the full strategy with the external review enabled, bounded by the effective caps, stopping the external review early after the effective patience count of consecutive unchanged rounds.
6. **No side effects.** The effective configuration equals the authored one everywhere except the four review knobs.
