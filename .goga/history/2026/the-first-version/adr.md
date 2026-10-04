# complex-build as a hook-only config-amendment preset tool

The PRD asks for a distributable goga tool package that gives every build of an adopting project a comprehensive review. We decided to build it strictly in the shape of the existing `simple-build` analog: a hook-only package — one subscription to the hard `config / amend_config` action under the hook name `review_presets`, no CLI, no runtime import of goga (platform types referenced under `TYPE_CHECKING` only) — because the platform's amendment contract already owns every semantic the PRD requires: authored-wins, silence detection, value-free summaries, and the hard fail-loud stop.

The hook buffers four unconditional `set` amendments — `build.review.strategy` = `full`, `build.review.max_iterations` = `5`, `build.review.additional.patience` = `2`, `build.review.additional.max_iterations` = `3` — and reads exactly one configuration leaf: the guard `build.review.strategy`. When the authored strategy is present and is not `full`, the hook raises; the hard action turns that into the single clean tool-named error that stops the command before anything launches and discards the whole contribution.

## Considered Options

- **Conditional gap-filling** (read all four leaves, contribute only the silent ones) — rejected. Authored-wins, including the explicit-zero cases the PRD calls out, is owned by the platform merge: silence means only the absence markers `None`/`{}`/`[]`; authored `0`/`False`/`""` are authored. Re-deriving that inside the hook would duplicate platform semantics and re-open the zero-semantics bug class for no benefit. The deliberate reads of the configuration are the guard leaf only.
- **A both-caps conflict guard and iteration-cap remapping** (`simple-build`-style) — rejected; the PRD scopes both caps as independent authored-wins knobs.
- **`force` amendments** — rejected; the tool must never overwrite authored values.
- **Tolerating a contradicting authored strategy** — rejected; the PRD demands fail-loud, and raising inside the hook is the platform's only hard-fail channel at configuration load.

## Consequences

- Authored values (explicit zeros included) win at their paths with zero tool-side logic; a `set` on a non-silent path is dropped by the merge silently — by design.
- The loader never intercepts an out-of-vocabulary authored strategy first: `strategy` is a structural string in the config model, so the guard is what stops any authored value other than `full`.
- Coexistence with other config-amending tools is entirely platform-governed (per-path precedence, the later tool winning among equal intents); the tool neither detects nor vetoes neighbors.
- Tests are contract unit tests on lightweight `ConfigAmendment` fakes — no goga runtime dependency, matching the import-clean facade policy. The package ships a maintainer-facing `.usages/comprehensive-review.md` (analog-style); the docs site stays scaffold-only.
- Release publishing is outside this decision; the change delivers a pip-installable package (`goga install --local .:complex-build`), and cutting versions follows the repository's standard release workflow.

## Terms

- **authored** — a value present in `.goga/config.yml` as loaded; explicit `0`/`False`/`""` are authored, never silent.
- **silent** — an absence marker of the loaded model: `None`, `{}`, `[]`, or an absent intermediate branch.
- **`set` / apply-where-silent** — the amendment form that applies only where the authored configuration is silent; authored-wins is owned by the merge layer.
- **`force` / override** — the amendment form that overwrites an authored value; forbidden for this tool.
- **hard action** — the `config/amend_config` error class: the first failing tool stops the command with a clean error naming the tool and the action, its whole contribution discarded.
- **hook-only tool** — a `goga_tool_*` package whose only facade callback is `register_hooks`; tool identity (`complex-build`) is assigned by the platform from the package name.

## Unresolved questions

- Module layout, CODEMANIFEST structure, and cell boundaries of the package (later architecture stages).
- The exact composition of the facade export beyond the subscription (hook function naming and signature).
- The design of the test fakes.
- The exact wording of the guard message (bounded by the value-free, path-naming constraint).
