# Package facade

The `goga_tool_complex_build` cell — the platform subscription and the single API surface of
the tool. The facade must stay import-clean: a broken import is fatal to every goga command.

## Platform subscription

```python
from goga_tool_complex_build import register_hooks

register_hooks(hooks)  # goga calls this when a command first reaches a hook checkpoint
```

The registration subscribes exactly one hook: address `config` / `amend_config`, name
`review_presets`. No CLI entry, no install lifecycle, no runtime import of goga — the platform
types are referenced under `TYPE_CHECKING` only.

### `register_hooks(hooks: HookRegistrar)`

Subscribe the tool's single review-presets hook to the configuration amendment action.

- `hooks`: the goga subscription surface delivered at registration — exposes
  `subscribe(domain, action, name, hook)`
- Subscribes the hook routine `review_presets` under domain `config`, action `amend_config`,
  hook name `review_presets` — exactly one subscription, unconditional
- Hook name stays unique per tool per address; no configuration or file reads during
  registration; subscribes to no other domain action

### `review_presets(context: ConfigAmendment)`

The amendment hook — contribute the four comprehensive-review presets and guard the authored
strategy.

- `context`: the per-tool read-and-amend view over the authored configuration

Algorithm:

1. Read the authored leaf `build.review.strategy` from the configuration of `context`; absent
   branches read as absent
2. If the authored value is present and is not `full` — raise an exception whose message
   names the path `build.review.strategy` and never the authored value
3. Buffer four apply-where-silent amendments through `context`: `build.review.strategy` set
   to `full`, `build.review.max_iterations` set to `5`, `build.review.additional.patience`
   set to `2`, `build.review.additional.max_iterations` set to `3`

The guard raise of step 2 happens before any amendment is buffered, and its message is the
fixed strategy-conflict message: authored value at `build.review.strategy` conflicts with the
tool's purpose; remove the authored strategy or uninstall the tool. The amendments are
unconditional — the deliberate read of the configuration is the guard leaf of step 1 only.
Authored-wins is owned by the merge layer and is never re-derived here. The exact write
footprint is the four leaf paths of step 3 and nothing else: no other configuration paths, no
tasks-pass settings, no environment values. The hook never validates agent presence and never
uses the override form of amendment — the presets never overwrite authored values.
Configuration values are never printed or embedded in any output or error message.

## The presets

| Path | Value |
|---|---|
| `build.review.strategy` | `full` |
| `build.review.max_iterations` | `5` |
| `build.review.additional.patience` | `2` |
| `build.review.additional.max_iterations` | `3` |

All four values are fixed constants; the tool defines no mapping between the iteration caps —
they are independent knobs that only receive their presets when silent. Beyond the presets
there is no tool-own configuration to tune them with. What an installed tool guarantees in
practice is documented in [Comprehensive review](../comprehensive-review.md).

## Preconditions and side effects

- The hook is a pure function of the delivered context: no state, no cache, no clock or
  environment reads; identical facts produce the identical contribution.
- No project file is ever created or modified; the presets exist only in the effective
  in-memory configuration of each run — the authored `.goga/config.yml` stays
  byte-identical.
- Failures surface as clean command errors through the hard action; the tool's whole
  contribution is discarded — nothing partial applies. The deliberate failure is the
  strategy conflict; a broken package import is the single remaining fatal case.
