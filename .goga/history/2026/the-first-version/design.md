# Design Document: `the-first-version`

## Contract Changes

### Changed CODEMANIFEST Files
- `goga_tool_complex_build/CODEMANIFEST`: **added** (new file, untracked against base `0.0.x` — the project's
  first cell; `goga schema` before this change was `[]`). Header: 4 file-form `Usages`, global `Annotations`,
  no `Imports`. Body: 2 Routines at `location: registration.py`. Footer: `Author: Goga`, `CreatedAt: 04/10/26`.

### New Entities
- `register_hooks(hooks: HookRegistrar)` — facade callback: subscribes the tool's single hook to the
  `config / amend_config` action. Location: `goga_tool_complex_build/registration.py`.
- `review_presets(context: ConfigAmendment)` — the hook: contributes four apply-where-silent review presets
  and guards the authored strategy. Location: `goga_tool_complex_build/registration.py`.

### Changed Entities
- None.

### Deleted Entities
- None.

### Usages and Annotations Changes
- None. All four header practices (`conventions`, `config_amendment`, `hook_registration`, `goga_dependency`)
  are declared, resolve to existing files under `.goga/usages/`, and are referenced in annotations.

## Applied Fixes

### Fixed CODEMANIFEST Defects
- None. Phase 3 validation and the Phase 4 tracing loop surfaced no CODEMANIFEST defects:
  - `goga lint` → `cells: 1 errors: 0`; `goga schema` → cell with exactly the two planned types.
  - DSL: structure (header → body → footer, `---` separators), key casing, `location: registration.py`
    (same level, `.py` extension, no traversal — `goga config language` = `python`), Routine form (no
    `methods`/`properties`, correct for single operations), no `::` mutations, no `->` embeddings, no `Imports`.
  - Cookbook: Routine selection correct; file-form `Usages` justified (extensive, shared, evolve independently);
    granularity single-phrase ("review presets for comprehensive builds"); every practice referenced in at
    least one annotation; every backtick reference resolves within the document (`hooks`, `context` signature
    variables; `review_presets` body type; four practice keys).
  - Interface ↔ Type: `HookRegistrar.subscribe(domain, action, name, hook)` and
    `ConfigAmendment.config` / `.set(path, value)` shapes verified against the installed platform source
    (goga 2.0.2) — see Code Stack Trace.
  - Interface ↔ Interface: `review_presets` declares exactly `context` — one of the two fixed offered hook
    names — so the platform's signature projection delivers it by keyword; `subscribe`'s `hook` parameter
    (`Callable[..., object]`) accepts the routine.

Implementation-level gaps (not contract defects — they are what this design specifies):
1. `registration.py` does not exist yet — both routines to implement.
2. `goga_tool_complex_build/__init__.py` is empty — the facade re-export required by global annotations is
   missing. Verified as **functionally required**, not stylistic: the platform's `call_register_hooks` imports
   the facade module and quietly skips a package whose facade lacks a callable `register_hooks`
   (no warning, no error) — without the re-export the tool would silently never register.
3. `pyproject.toml` test extra lacks the `goga>=2.0` requirement mandated by `goga_dependency`.
4. No `tests/` directory exists — full test coverage gap, addressed by the Test Stack Trace below.

## Entity Interaction and Data Flow

### Interaction Diagram

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
   │  subscribe("config","amend_config","review_presets", review_presets) │
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

### Data Flows

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

### Entity Dependencies
- `register_hooks` depends on `review_presets` (passes it as the `hook` argument — same module, defined at
  import time, no initialization order concern).
- `review_presets` depends on the delivered `context` object only (structural: attribute reads + `set` calls).
- The facade `__init__.py` depends on `registration.py` (relative import, re-export by identity).
- No inter-cell dependencies (`dependencies: {}` in schema); the goga platform relationship is runtime delivery,
  referenced under `TYPE_CHECKING` only.

## Code Stack Trace

All traces verified against the installed platform source (goga 2.0.2, `/opt/goga/.../site-packages/goga/`)
and by an end-to-end scratch run of the exact contract shape (silent config, authored config, conflict config,
real registrar) — all checkpoints passed empirically.

### Trace: `register_hooks`

#### Chain
1. **Input**: a command reaches its first hook checkpoint of the run (or `goga hooks` inspection).
   `HookRegistry.build_once()` enumerates tool packages, imports the facade `goga_tool_complex_build`, and
   calls `register_hooks(HookRegistrar(tool="complex-build"))` → checkpoint: facade import succeeds without
   goga installed (module has no runtime goga import; `TYPE_CHECKING` only) — **passed** (verified: platform
   imports the facade module itself; a missing callback is a quiet skip, so the re-export is required).
2. **Step**: `hooks.subscribe("config", "amend_config", "review_presets", review_presets)` →
   checkpoint: address resolves in `declared_actions` (`config.amend_config`, `error_class="hard"`) —
   **passed** (verified in catalog and by real-registrar run: 1 subscription, 0 rejections); `name` non-empty
   and unique per tool per address (single registration) — **passed**; `hook` callable, keyword-capable
   `context` parameter — **passed** (verified: `build_hook_arguments` projects exactly `{'context': proxy}`).
3. **Step**: the registrar appends `Subscription(tool="complex-build", domain="config", action="amend_config",
   name="review_presets", hook=review_presets)` → checkpoint: a wrong address/empty name/repeat would be
   **rejected as data with a log warning, never raised** — the routine passes none of those paths.
4. **Output**: `None`. One subscription lives in the run registry; no return value, no side effects beyond
   the registration record.

#### Checkpoint Summary
- facade discoverability: **passed** — `register_hooks` is present on the package facade via re-export.
- address validity: **passed** — `config / amend_config` is declared, hard.
- envelope validity: **passed** — non-empty unique name, callable hook.
- subscribe-arity/type alignment: **passed** — `subscribe(domain: str, action: str, name: str, hook:
  Callable[..., object]) -> None` matches the call exactly.

### Trace: `review_presets`

#### Chain
1. **Input**: the `amend_config` checkpoint fires at the load moment of `.goga/config.yml`. The platform
   constructs `ConfigAmendment(config=_read_only_snapshot(authored ProjectConfig))`, wraps it with
   `wrap_context` (reads and calls pass through; attribute assignment/deletion raise `AttributeError`), and
   calls `review_presets(context=proxy)` → checkpoint: only declared offered names are delivered
   (`{"context": proxy}`) — **passed** (verified with the real `build_hook_arguments`).
2. **Step**: read the strategy chain — `config = context.config` (proxy passthrough → the frozen read-only
   `ProjectConfig` snapshot), `build = config.build` (`BuildConfig | None`; the model always materializes the
   field, `None` when the section is absent), `review = build.review if build is not None else None`
   (`ReviewConfig | None`), `strategy = review.strategy if review is not None else None`
   (`str | None`) → checkpoint: absent branches read as `None` without `AttributeError` — **passed**
   (verified: `ProjectConfig.build`, `ReviewConfig.strategy`, `ReviewConfig.additional` are model fields,
   `None` defaults on the optional sections; the read-only snapshot preserves field names via `replace()`).
3. **Step**: guard — `if strategy is not None and strategy != "full": raise ValueError(<fixed message>)`
   → checkpoint: presence test uses `None` (the model's silence marker) so authored emptiness (`""`) counts
   as present-and-conflicting — **passed** (verified in the model: `strategy: str | None = None`, no
   empty-string normalization); the message names the path `build.review.strategy` and never the value —
   **passed** (verified: sentinel value absent from the raised message); the raise precedes every `set` —
   **passed** (verified: 0 buffered amendments on the conflict path); the platform wraps the raise as
   `ValueError("hook review_presets of tool complex-build failed on config.amend_config: …")` naming the
   hook, the tool, and the action — **passed** (verified in the checkpoint source).
4. **Step**: buffer four amendments — `context.set("build.review.strategy", "full")`,
   `context.set("build.review.max_iterations", 5)`, `context.set("build.review.additional.patience", 2)`,
   `context.set("build.review.additional.max_iterations", 3)` (the proxy resolves `set` to the bound method;
   each call stores `PathAmendment(path, intent="set", value)` in the tool's private buffer, a later call on
   the same path replacing the earlier one) → checkpoint: all four paths are model-known typed leaves in the
   merge's configuration type tree with matching value kinds — **passed** (verified in the type tree:
   `ReviewConfig.strategy` `_scalar(str)`, `ReviewConfig.max_iterations` `_scalar(int)`,
   `AdditionalReviewConfig.patience` `_scalar(int)`, `AdditionalReviewConfig.max_iterations` `_scalar(int)`);
   unconditional buffering is safe — authored-wins is applied later by the merge, never here — **passed**
   (verified: authored `strategy: full` still receives the buffered `set`, which the merge then drops).
5. **Output**: `None`. The tool's buffer carries exactly four `set` amendments; the checkpoint commits it as
   one `ToolAmendment` and merges → checkpoint: effective composition — **passed** (verified end-to-end on a
   silent base: applied = 4 records, effective `strategy=full, max_iterations=5, patience=2,
   additional.max_iterations=3`, summary lines name `complex-build` with four `set` lines, the authored
   object untouched).

#### Checkpoint Summary
- hook-signature projection: **passed** — `context` is a fixed offered name; delivered by keyword.
- read footprint: **passed** — exactly the `build.review.strategy` chain; nothing else is read.
- guard semantics: **passed** — present-and-≠-`full` raises; `None` (silent) and `"full"` do not.
- guard ordering: **passed** — raise strictly before the first `set`.
- write footprint: **passed** — exactly the four leaf paths, intent `set` only, `force` never called.
- value/path structural validity: **passed** — all four resolve in the merge type tree with matching kinds.
- authored-wins ownership: **passed** — merge-layer responsibility; the hook never re-derives it.

## Algorithm Design

### `register_hooks`

**Responsibility**: the platform facade callback — declare the tool's single subscription on the
configuration amendment action.

**Algorithm:**
```
1. call `hooks`.subscribe with
   domain="config", action="amend_config", name="review_presets", hook=`review_presets`
   → one Subscription(tool="complex-build", …) appended to the registrar; return None
```

**Errors:**
- none raised by the routine. An invalid envelope would be refused by the registrar as data with a log
  warning (registration skipped) — unreachable here: the address is declared, the name is non-empty and used
  once, the hook is the module-level routine.

**Edge Cases:**
- called once per run per registry build (registration is never cached by the platform; the routine itself is
  idempotent — a second call would be rejected as "repeated name on the same address", which cannot occur
  through the normal one-registry-per-run lifecycle).
- the `hooks` surface is tool-scoped (`tool="complex-build"` assigned by the platform from the package name);
  the routine never names its own tool identity.

### `review_presets`

**Responsibility**: the configuration amendment hook — contribute the four comprehensive-review presets
where the authored configuration is silent, and fail the run on a deliberate strategy conflict.

**Algorithm:**
```
1. read the strategy leaf of the authored configuration:
   config  = `context`.config
   build   = config.build                       (BuildConfig | None)
   review  = build.review    when build  else None
   strategy= review.strategy when review else None
   → strategy: str | None — absent branches read as None
2. IF strategy is not None AND strategy ≠ "full":
   - raise ValueError with the fixed message:
     "authored value at build.review.strategy conflicts with the tool's purpose; "
     "remove the authored strategy or uninstall the tool"
   - the message names the path only — never the authored value
   - nothing has been buffered at this point
3. buffer four amendments through `context`.set (apply-where-silent intent), in order:
   build.review.strategy             = "full"
   build.review.max_iterations       = 5
   build.review.additional.patience  = 2
   build.review.additional.max_iterations = 3
   → return None; the merge layer resolves authored-wins later
```

**Errors:**
- `ValueError` (authored strategy present and ≠ `"full"`) → raised before any amendment is buffered → the
  hard action stops the command; the platform wraps it naming the hook (`review_presets`), the tool
  (`complex-build`), and the action (`config.amend_config`); the tool's whole contribution is discarded →
  the consumer observes a clean command error that contains the path `build.review.strategy` and never a
  configuration value.

**Edge Cases:**
- absent `build` section, or `build` present with absent `review` → strategy reads `None` → silent → presets
  apply; the merge materializes the missing branches.
- authored `strategy: null` → model `None` → silent → presets apply (authored YAML null is the silence marker).
- authored `strategy: ""` → authored emptiness is authored, not silent → present and ≠ `"full"` → conflict.
- authored `strategy: full` → no raise; the `set` on `build.review.strategy` is still buffered
  (unconditional) and dropped by the merge (authored-wins).
- authored non-string strategy value (e.g. a number or boolean) → present and ≠ `"full"` → conflict; no type
  validation is performed (out of scope by constraint).
- authored values on the other three leaves (including explicit zeros) → irrelevant to the hook (it never
  reads them); the merge drops the corresponding `set`s silently.

## Cross-cutting Concerns

- **Error handling**: single raise site — the strategy guard (`ValueError`, fixed message, path-only).
  No exception handling inside the cell: the routine lets the raise propagate to the hard-action checkpoint,
  which owns the wrapping, the tool/action naming, and the contribution discard. No error swallowing, no
  fallback paths, no custom exception types.
- **Logging**: none, by design. The platform owns every observable output: registration refusals (log
  warning), the amendment summary (stderr, value-free), and failure errors. The cell adds no logger — this
  satisfies the constraint "never print or embed configuration values in any output" and avoids duplicating
  platform-owned reporting; there is no business event in a four-constant contribution worth logging.
- **Validation**: the strategy guard only — presence (`is not None`) plus inequality with `"full"`. No other
  leaf is read, validated, or type-checked (constraint: "Do not validate any leaf beyond the strategy
  guard"); structural path/value validation belongs to the platform merge.
- **Caching**: none. The hook recomputes its four constants on every delivery; registration is rebuilt per
  run by the platform (never cached). No module-level mutable state exists.
- **Concurrency**: stateless routines over delivered objects; no shared mutable state, no module globals
  mutated, the `self` tool context is not declared and not used. Safe under any delivery threading because
  all state lives in the per-tool view the platform constructs.

## Usages Analysis

### `conventions`
- **What it provides**: mandatory Python engineering rules — 3.10+ compatibility, relative intra-package
  imports, Google-style docstrings, blank-line block formatting, structured logging policy, and the full
  testing standard (structure, naming, fixtures, mock boundaries, parametrized boundary tests, validation
  commands).
- **Where used**: global annotations — applies to both routines, the facade, and every test file.
- **Why chosen**: the project-wide code mandate; also injected by `.goga/config.yml` `codemanifest.annotations`.
- **How exactly**: `registration.py` and `__init__.py` use relative imports (`from .registration import …`),
  Google-style docstrings with `Args`/`Raises` sections, one-blank-line block separation; tests live in
  `tests/test_registration.py` / `tests/test_init.py` mirroring the source, fixtures in `tests/conftest.py`,
  mocks only at the platform boundary; `pytest tests/ -x` and `ruff check goga_tool_complex_build/` are the
  validation commands.

### `hook_registration`
- **What it provides**: the facade-callback contract for tool packages — the three possible callbacks, the
  `hooks.subscribe(domain, action, name, hook)` envelope, hook-name uniqueness, offered-name parameter
  delivery (`context`, `self`), run timing (never cached), and failure behavior (envelope rejection as data).
- **Where used**: global annotations and the `register_hooks` annotation.
- **Why chosen**: it is the authoritative specification of the registration surface the routine calls.
- **How exactly**: one `subscribe("config", "amend_config", "review_presets", review_presets)` call; the hook
  declares only `context`, so the platform delivers exactly that by keyword.

### `config_amendment`
- **What it provides**: the config domain action spec — the `config / amend_config` address (hard), the
  `ConfigAmendment` read-and-amend view (`config` reads, `set`/`force` buffering), silence markers
  (`None`, `{}`, `[]` vs authored `False`, `""`), merge rules (authored-wins for `set`, `force` beats `set`,
  later-tool-wins, tools mutually blind), failure treatment, and the value-free run summary.
- **Where used**: global annotations and the `review_presets` annotation.
- **Why chosen**: it specifies the exact view the hook receives and the semantics of the buffered intents.
- **How exactly**: reads through `context.config` (attribute chain with `None` guards), contributions through
  `context.set(path, value)` only — `force` is never called; authored-wins is left to the merge layer.

### `goga_dependency`
- **What it provides**: the dependency policy — empty runtime `[project].dependencies`, no runtime goga
  import, platform types under `typing.TYPE_CHECKING` only, goga declared exclusively in the `test` extra as
  `goga>=2.0` (floor at the platform line, no upper cap).
- **Where used**: global annotations.
- **Why chosen**: it governs the package metadata and import structure of the hook-only cell.
- **How exactly**: `registration.py` uses `from __future__ import annotations` plus a `TYPE_CHECKING` block
  importing `HookRegistrar` and `ConfigAmendment`; `pyproject.toml` gains `"goga>=2.0"` in
  `[project.optional-dependencies].test`; version drift is surfaced by the platform usages pin
  (`usages.github.goga.ref: 2.0.x`), not by the package metadata.

### Imported Usages
- None — the cell has no `Imports` (single-node project graph).

## `.usages/` Update

### Cell: `goga_tool_complex_build`

#### Existing Files — Consistency
- **`comprehensive-review.md`** → `goga_tool_complex_build/.usages/comprehensive-review.md`
  - Status: **current** — no changes needed.
  - Verified against the contract and the platform: the four path/value pairs match the `review_presets`
    annotation step 3 exactly; the authored-wins section (including explicit zeros, independent caps)
    matches the merge semantics verified end-to-end (authored `patience: 4`, `additional.max_iterations: 0`
    produce effective `full 5 4 0` with one applied amendment — precisely the document's example); the
    conflict section matches the guard plus the hard-action wrap (command stops, error names tool, action,
    and path, value never printed, nothing applied); the side-effects section matches the verified behavior
    (authored file untouched, deterministic reruns); both contract routines are covered from the consumer
    perspective (the single subscription is described as "the tool is hook-only", the presets as the
    guarantee table).
  - Additions needed: none.
  - Updates needed: none.

#### New Files (if any)
- None — the cell exposes one functional domain (comprehensive-review presets); a single usage file covers
  it. Per the decision rules, changes within the existing domain would supplement this file; no new domain
  exists.

## Test Stack Trace

### General Setup
- Test environment: a virtualenv **outside the project at `/opt/project`** with the package installed
  editable plus its test extra (`goga>=2.0`, pytest, pytest-cov, pytest-mock, ruff). goga is available to
  tests by design; the runtime import-cleanliness is tested explicitly in a goga-blocked subprocess.
- Shared fixtures (`tests/conftest.py`):
  - `project_config(build=…)` — builds a real `ProjectConfig(language="python", image=None,
    dockerfile=None, build=build, pipeline=None)`; real platform models keep the authored-value shapes
    truthful (frozen dataclasses, `None` absence markers).
  - `recording_view(request)` — a `_RecordingAmendment(ConfigAmendment)` subclass overriding `set`/`force`
    to append `(path, value)` / `("force", path, value)` records and delegate to `super()`; exposes
    `.set_calls`, `.force_calls`, and the real inherited buffer.
  - `trap` — an object whose every attribute access raises `AssertionError`, planted into unread
    configuration branches to prove the read footprint.
- Unit tests use the recording view directly; delivery tests use the real `wrap_context` +
  `build_hook_arguments` + `merge_config_amendments` primitives (imported from the platform modules where
  they live). No network, no filesystem, no subprocess except the facade-import check.

### Source File Registry
- `goga_tool_complex_build/registration.py` — both routines under test.
- `goga_tool_complex_build/__init__.py` — facade re-export under test.

---

### Positive Tests

#### `test_register_hooks_subscribes_single_hook_to_config_amend_config`

**Setup**: a `_FakeRegistrar` exposing `subscribe(domain, action, name, hook)` that appends
`(domain, action, name, hook)` to `calls`; no other methods. Class `TestRegisterHooks` in
`tests/test_registration.py`.

**Input**: `register_hooks(_FakeRegistrar())`

**Trace**:
```
register_hooks(fake)
  → fake.subscribe("config", "amend_config", "review_presets", review_presets)
    side effect: calls == [("config", "amend_config", "review_presets", <function review_presets>)]
  → return None
```

**Assertions**:
```
len(fake.calls) == 1
fake.calls[0][:3] == ("config", "amend_config", "review_presets")
fake.calls[0][3] is registration.review_presets      # by identity, not by name
```

**Sufficiency**: pins the exact subscription address and the hook-name uniqueness requirement; the identity
check prevents registering a same-named wrapper instead of the contract routine. Regression: a wrong domain
or action string would be silently rejected by the real registrar (a quiet skip) — this test is the only
place that would catch it deterministically.

---

#### `test_register_hooks_envelope_accepted_by_real_registrar`

**Setup**: real platform registrar `HookRegistrar(tool="complex-build")` imported from
`goga.hooks.tools.registration`. Class `TestRegisterHooks`.

**Input**: `register_hooks(registrar)`

**Trace**:
```
register_hooks(registrar)
  → registrar.subscribe(...)                      # resolves config.amend_config in declared_actions
    side effect: one Subscription appended; rejections stay empty
  → registrar.subscriptions == [Subscription(tool="complex-build", domain="config",
                                             action="amend_config", name="review_presets", hook=…)]
```

**Assertions**:
```
len(registrar.subscriptions) == 1
[(s.domain, s.action, s.name) for s in registrar.subscriptions] == [("config", "amend_config", "review_presets")]
registrar.rejections == []
```

**Sufficiency**: proves the envelope survives the real address catalog — an unknown address or a malformed
name would land in `rejections` as data with only a log warning. Regression: a platform catalog rename of the
action would otherwise make the tool silently stop applying.

---

#### `test_review_presets_buffers_four_presets_on_silent_config`

**Setup**: `project_config(build=None)` — fully silent review branches. Fixture `view =
_RecordingAmendment(config=project_config(build=None))`. Class `TestReviewPresets`.

**Input**: `review_presets(view)`

**Trace**:
```
review_presets(view)
  → config = view.config                          # ProjectConfig, build is None
  → build = None → review = None → strategy = None
  → guard: strategy is None → no raise
  → view.set("build.review.strategy", "full")           # record 1, intent "set"
  → view.set("build.review.max_iterations", 5)          # record 2
  → view.set("build.review.additional.patience", 2)     # record 3
  → view.set("build.review.additional.max_iterations", 3)  # record 4
  → return None
```

**Assertions**:
```
view.set_calls == [
    ("build.review.strategy", "full"),
    ("build.review.max_iterations", 5),
    ("build.review.additional.patience", 2),
    ("build.review.additional.max_iterations", 3),
]
view.force_calls == []
```
(exact list equality — pins count, order, paths, values, and the absence of any other write)

**Sufficiency**: the happy path and the complete write footprint in one assertion. Regression: an extra
amendment, a wrong value, a swapped order (the order is the summary-line order), or a `force` call would all
fail here.

---

#### `test_review_presets_with_authored_full_strategy_buffers_unconditionally`

**Setup**: `project_config(build=BuildConfig(review=ReviewConfig(strategy="full")))`; recording view over it.

**Input**: `review_presets(view)`

**Trace**:
```
review_presets(view)
  → strategy = "full"                             # present, equal → guard passes
  → four set calls exactly as in the silent case, including ("build.review.strategy", "full")
  → return None
```

**Assertions**:
```
view.set_calls == [(…four exact pairs as above…)]
```

**Sufficiency**: pins the "amendments are unconditional" requirement — the hook must not condition the
strategy `set` on the authored value; authored-wins is the merge layer's job. Regression: a "smart"
implementation skipping the redundant `set` would pass every merge outcome yet violate the contract.

---

#### `test_review_presets_through_real_delivery_projection`

**Setup**: recording view over `project_config(build=None)`; real `proxy = wrap_context(view)`; real
`args = build_hook_arguments(review_presets, proxy, object())`. Class `TestDelivery`.

**Input**: `review_presets(**args)`

**Trace**:
```
build_hook_arguments(review_presets, proxy, object())
  → {"context": proxy}                            # only the declared offered name
review_presets(context=proxy)
  → proxy.config → passthrough read → view.config (frozen snapshot)
  → proxy.set(…) → passthrough call → _RecordingAmendment.set → record + super().set
  → real buffer holds four PathAmendment(intent="set")
```

**Assertions**:
```
sorted(args) == ["context"]
view.set_calls == [(…four exact pairs as above…)]
[(a.path, a.intent, a.value) for a in view._amendments.values()] == [
    ("build.review.strategy", "set", "full"),
    ("build.review.max_iterations", "set", 5),
    ("build.review.additional.patience", "set", 2),
    ("build.review.additional.max_iterations", "set", 3),
]
```

**Sufficiency**: proves the routine works through the real mediation stack — the write-blocking proxy
transparently passing reads and `set` calls, and the signature projection delivering `context` by keyword.
Regression: a hook that assigns to the context, declares a non-offered parameter, or relies on positional
delivery would only fail here.

---

#### `test_presets_merge_into_effective_review_config`

**Setup**: `base = project_config(build=None)`; deliver `review_presets` into a real `ConfigAmendment` over
`base`; build `ToolAmendment(tool="complex-build", amendments=list(view._amendments.values()))`; call the real
`merge_config_amendments(base, [contribution])`. Class `TestDelivery`.

**Input**: the overlay returned by the merge.

**Trace**:
```
merge_config_amendments(base, [contribution])
  → VALIDATE: four paths resolve in the type tree with matching kinds
  → RESOLVE: base silent at all four → all four set amendments survive
  → COMPOSE: build / review / additional branches materialize bottom-up
  → COLLECT: four AppliedAmendment(tool="complex-build", intent="set")
  → ConfigOverlay
```

**Assertions**:
```
review = overlay.config.build.review
review.strategy == "full"
review.max_iterations == 5
review.additional.patience == 2
review.additional.max_iterations == 3
len(overlay.applied) == 4
all(r.tool == "complex-build" and r.intent == "set" for r in overlay.applied)
overlay.summary_lines == [
    "config amendments: 4 applied",
    "- complex-build set build.review.strategy",
    "- complex-build set build.review.max_iterations",
    "- complex-build set build.review.additional.patience",
    "- complex-build set build.review.additional.max_iterations",
]
base.build is None          # the authored object is untouched
```

**Sufficiency**: the end-to-end guarantee of the cell usage document — the exact table a maintainer relies
on, plus the value-free summary format. Regression: a value of the wrong kind (e.g. `"5"` instead of `5`)
would fail the merge VALIDATE step, and any path drift would fail here first. Verified empirically: this is
precisely the behavior the scratch run produced.

---

#### `test_facade_reexports_contract_api_by_identity`

**Setup**: import the installed package. Class `TestInit` in `tests/test_init.py`.

**Input**: `import goga_tool_complex_build as facade`

**Trace**:
```
facade import → __init__.py → from .registration import register_hooks, review_presets
  → facade.register_hooks, facade.review_presets bound
```

**Assertions**:
```
facade.__all__ == ["register_hooks", "review_presets"]
facade.register_hooks is registration.register_hooks
facade.review_presets is registration.review_presets
```

**Sufficiency**: the platform reads `register_hooks` off the facade module — a missing re-export is a quiet
skip with no warning, so the tool would silently never register. Regression: dropping or renaming the
re-export, or shadowing it with a wrapper, fails here.

---

### Negative Tests

#### `test_review_presets_raises_value_error_on_conflicting_strategy_before_any_set`

**Setup**: `project_config(build=BuildConfig(review=ReviewConfig(strategy="short")))`; recording view.

**Input**: `pytest.raises(ValueError, review_presets, view)` capturing `excinfo`

**Trace**:
```
review_presets(view)
  → strategy = "short"                            # present and ≠ "full"
  → raise ValueError("authored value at build.review.strategy conflicts with the tool's purpose; "
                     "remove the authored strategy or uninstall the tool")
    side effect: nothing buffered — the raise precedes every set
```

**Assertions**:
```
str(excinfo.value) == ("authored value at build.review.strategy conflicts with the tool's purpose; "
                      "remove the authored strategy or uninstall the tool")
"build.review.strategy" in str(excinfo.value)
view.set_calls == []
view.force_calls == []
```

**Sufficiency**: pins all three guard requirements at once — the exception type, the exact fixed message
naming the path, and the strict before-any-amendment ordering (the whole contribution must be discardable).
Regression: buffering-then-raising would leave partial state; a message naming the value would leak
configuration content into output.

---

#### `test_review_presets_error_message_never_contains_authored_value`

**Setup**: `project_config(build=BuildConfig(review=ReviewConfig(strategy="s3cr3t-strategy-value")))` — a
distinctive sentinel unlikely to appear in any fixed wording; recording view.

**Input**: `pytest.raises(ValueError, review_presets, view)` capturing `excinfo`

**Trace**:
```
review_presets(view)
  → strategy = "s3cr3t-strategy-value"            # present and ≠ "full"
  → raise ValueError(fixed message)               # the value never enters the message
```

**Assertions**:
```
"s3cr3t-strategy-value" not in str(excinfo.value)
"build.review.strategy" in str(excinfo.value)
view.set_calls == []
```

**Sufficiency**: the value-leak constraint is a secrecy property of the platform ("goga never prints a
configuration value") — the guard must not become the leak. A plain word like "short" could collide with
future wording; the sentinel makes the check sound. Regression: any f-string interpolation of the authored
value into the message fails here.

---

#### `test_facade_imports_without_goga_installed`

**Setup**: a subprocess with every `goga` module blocked: `sys.modules["goga"] = None` (and the known
submodule keys) installed before the import, project root on `sys.path` (run with `cwd` at the repository
root, `sys.executable -c`). Class `TestInit`.

**Input**: the subprocess script imports the package and prints `__all__` plus the two callables.

**Trace**:
```
subprocess: python -c "<block goga in sys.modules; import goga_tool_complex_build; print(__all__)>"
  → __init__.py → from .registration import …
  → registration.py: from __future__ import annotations — signatures never evaluated at runtime
  → TYPE_CHECKING block never executes at runtime
  → import succeeds with no goga importable
```

**Assertions**:
```
result.returncode == 0
"register_hooks" in result.stdout and "review_presets" in result.stdout
```

**Sufficiency**: the dependency policy — a broken facade import is the single fatal case for every goga
command, and the package must install into environments without goga. Regression: a runtime `import goga`
(or an un-guarded annotation reference, which raises `NameError` at `def` time) fails only here. Verified
mechanism: `None` in `sys.modules` makes `import goga` raise `ImportError`.

---

### Edge Case Tests

#### `test_review_presets_authored_empty_string_strategy_raises`

**Setup**: `project_config(build=BuildConfig(review=ReviewConfig(strategy="")))` — authored emptiness is
authored, not silent (`False`, `""` are authored per the merge markers). Recording view.

**Input**: `pytest.raises(ValueError, review_presets, view)`

**Trace**:
```
review_presets(view)
  → strategy = ""                                 # present (not None) and ≠ "full"
  → raise ValueError(fixed message)
```

**Assertions**:
```
str(excinfo.value) == <the fixed message>
view.set_calls == []
```

**Sufficiency**: distinguishes the presence test (`is not None`) from a falsy test — a "not strategy" guard
would silently accept the empty string and buffer a preset over an authored leaf. Regression: weakening the
guard to truthiness fails here.

---

#### `test_review_presets_non_string_authored_strategy_raises`

**Setup**: parametrized over the wrong-type boundary values `5`, `True`, `1.5` —
`project_config(build=BuildConfig(review=ReviewConfig(strategy=value)))` — the model stores scalars
verbatim with no runtime type validation; recording view. Class `TestReviewPresets`.

**Input**: `pytest.raises(ValueError, review_presets, view)` for each parametrized value

**Trace**:
```
review_presets(view)
  → strategy = <value>          # present (not None), not equal to "full"
  → raise ValueError(fixed message)   # before any set
```

**Assertions**:
```
str(excinfo.value) == <the fixed message>
view.set_calls == []
```

**Sufficiency**: the invalid-types boundary of `conventions` — the presence test `is not None` must treat
a non-string scalar as authored-and-conflicting; the model stores it verbatim, so only the guard decides.
Regression: narrowing the guard to string values (an `isinstance` check) silently buffers a preset over a
malformed authored leaf and fails here.

---

#### `test_review_presets_absent_review_branch_with_present_build_section`

**Setup**: `project_config(build=BuildConfig(agent="claude"))` — `build` present, `review` absent (`None`).

**Input**: `review_presets(view)` over that config.

**Trace**:
```
review_presets(view)
  → build = BuildConfig(agent="claude")           # present
  → review = None → strategy = None               # the absent intermediate branch reads as absent
  → guard passes → four set calls
```

**Assertions**:
```
view.set_calls == [(…four exact pairs as above…)]
```

**Sufficiency**: the None-chain must handle the half-present branch — accessing `build.review.strategy`
directly would raise `AttributeError` on this configuration. Regression: a naive unguarded chain fails here.

---

#### `test_review_presets_reads_strategy_chain_only`

**Setup**: `project_config` with unread branches planted with the `trap` object (any attribute access raises
`AssertionError`): `pipeline=trap`, and a `BuildConfig(env={}, review=ReviewConfig(strategy=None,
additional=None, env=…))` where `additional` is `None`; `commands=trap` where the model allows.

**Input**: `review_presets(view)` over that config.

**Trace**:
```
review_presets(view)
  → reads config.build, build.review, review.strategy — and nothing else
  → trap branches are never touched → no AssertionError
  → four set calls
```

**Assertions**:
```
view.set_calls == [(…four exact pairs as above…)]      # completing without tripping the traps
```

**Sufficiency**: proves the read footprint is the guard leaf's chain alone — the contract's "deliberate
reads of the configuration are the guard leaf of step 1 only". Regression: any added configuration read
(agent detection, knob inspection) trips a trap and fails here.

---

#### `test_presets_merge_honors_authored_wins_on_authored_leaves`

**Setup**: `base = project_config(build=BuildConfig(review=ReviewConfig(strategy=None, additional=
AdditionalReviewConfig(patience=4, max_iterations=0))))` — authored `patience: 4` and authored zero
`additional.max_iterations`, everything else silent; deliver and merge as in the merge test. Class
`TestDelivery`.

**Input**: the overlay returned by `merge_config_amendments(base, [contribution])`.

**Trace**:
```
review_presets(view) → four unconditional set calls buffered
merge_config_amendments(base, [contribution])
  → RESOLVE: authored at patience and additional.max_iterations → those two set amendments dropped
  → applied: strategy (authored None → silent) and review max_iterations
  → COMPOSE: authored 4 and 0 preserved
```

**Assertions**:
```
review = overlay.config.build.review
review.strategy == "full"
review.max_iterations == 5
review.additional.patience == 4
review.additional.max_iterations == 0
[r.path for r in overlay.applied] == ["build.review.strategy", "build.review.max_iterations"]
```

**Sufficiency**: documents at merge level that unconditional buffering is safe — authored values (including
explicit zeros, which are authored rather than silent) win and the presets never overwrite them. Regression:
a `force` call or a conditional skip would change either the applied set or the effective values. Verified
empirically: the scratch run produced exactly these applied paths and effective values.

---

#### `test_tool_amends_through_real_checkpoint`

**Setup**: `config = ProjectConfig(language="python", image=None, dockerfile=None, build=None,
pipeline=None)`; the package installed editable in the `/opt/project` venv (the only `goga_tool_*` package
of the environment contributing to the config domain); real `ConfigHooks` from `goga.config.hooks.events`.
Class `TestCheckpointIntegration` in `tests/test_registration.py`.

**Input**: `overlay = ConfigHooks().amend_config(config=config)`

**Trace**:
```
ConfigHooks().amend_config(config)
  → build_once: enumerate_tool_packages → [goga_tool_complex_build]
  → import facade → register_hooks(HookRegistrar(tool="complex-build"))
  → one subscription (config / amend_config / review_presets)
  → per-tool read-only snapshot → wrap_context → {"context": proxy}
  → review_presets(context=proxy) → four set calls → ToolAmendment commit
  → merge_config_amendments → ConfigOverlay
```

**Assertions**:
```
review = overlay.config.build.review
review.strategy == "full" and review.max_iterations == 5
review.additional.patience == 2 and review.additional.max_iterations == 3
records = [r for r in overlay.applied if r.tool == "complex-build"]
len(records) == 4 and all(r.intent == "set" for r in records)
"- complex-build set build.review.strategy" in overlay.summary_lines
config.build is None          # the authored object is untouched
```

**Sufficiency**: the only test exercising the real registration path — enumeration discovers the installed
package by name, imports the facade, and derives the tool identity. Assertions filter by the tool name so a
foreign `goga_tool_*` package that does not touch the config domain cannot break the test. Regression:
packaging/name drift (module renamed, distribution/module mismatch, facade dropped from `packages.find`)
silently disables the tool with no warning anywhere; unit tests import the module directly and cannot
catch it.

---

## Additional Instructions for the Implementation Agent

- **Environment**: use a virtualenv **outside the project at `/opt/project`** for all development commands —
  create it if missing, install `pip install -e '.[test]'` there, and run `pytest tests/ -x` and
  `ruff check goga_tool_complex_build/` from it. Never commit a venv into the project tree.
- **Deliverables** — create exactly these files, leave everything else untouched:
  - `goga_tool_complex_build/registration.py` — both routines (Algorithm Design above); module docstring;
    `from __future__ import annotations`; `TYPE_CHECKING` block importing `HookRegistrar` from
    `goga.hooks.tools.registration` and `ConfigAmendment` from `goga.config.hooks.amendments` (verified
    paths in goga 2.0.2 — neither name is exported by the `goga.hooks` / `goga.config` facades); no runtime
    goga import; no logging; no print; Google-style docstrings with `Args`/`Raises`.
  - `goga_tool_complex_build/__init__.py` — module docstring, `from .registration import register_hooks,
    review_presets`, `__all__ = ["register_hooks", "review_presets"]`. Keep it import-clean without goga.
  - `tests/__init__.py`, `tests/conftest.py` (shared fixtures), `tests/test_registration.py`,
    `tests/test_init.py` — per the Test Stack Trace and the conventions' structure rules.
  - `pyproject.toml` — add `"goga>=2.0"` to `[project.optional-dependencies].test` (the single goga
    requirement, test-only, no upper cap); leave `[project].dependencies` empty.
- **Do not modify** `goga_tool_complex_build/CODEMANIFEST` or `goga_tool_complex_build/.usages/
  comprehensive-review.md` — both are verified current; the CODEMANIFEST is the contract this design
  implements.
- **Fixed literal**: the guard message is the exact two-line string specified in the `review_presets`
  algorithm; tests pin it by full equality. Do not reword, interpolate values, or add tool/action names
  (the platform wrapper supplies those).
- **Order matters**: keep the four `set` calls in the specified order — buffer order becomes the
  summary-line order consumers see.
- **Validation** (all from the `/opt/project` venv): `pytest tests/ -x` green; `ruff check
  goga_tool_complex_build/` clean; facade check `python -c "from goga_tool_complex_build import
  register_hooks, review_presets"` succeeds in a plain interpreter; the goga-blocked subprocess check
  passes.
