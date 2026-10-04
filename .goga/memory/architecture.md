# Project rules

## Guard-before-contribution ordering

In tooling hooked into abort-on-raise actions, where a raised error cancels the entire command and discards the tool's contribution, all conflict and precondition guards must fire before any contribution is buffered, so a failure can never leave a partially applied contribution.

## Value-free diagnostics

Every piece of tool-produced feedback (error messages, amendment summaries, any output) may name configuration paths but must never print or embed configuration values; messages stay fixed and value-free even where including a value would make diagnosis easier.

## Silent-leaf contribution semantics

Tool contributions exclusively fill configuration leaves that the authored file leaves silent; authored values win independently per path — including placeholder-like silence markers — the authored file is never modified, and authored-wins merging is owned by the platform layer rather than re-implemented inside the tool.

## Fixed minimal contract footprint

A routine's deliberate configuration reads and writes form a closed, agreed set; no additional leaves are validated, no related values are remapped, and no neighboring configuration-modifying tools are detected or vetoed — widening the footprint "for safety" is rejected.

## Host-decoupled runtime

A package discovered by the host platform must import cleanly whether or not that platform is installed: platform types are referenced only in static type-checking contexts, runtime dependencies remain empty, and the host platform is confined to test-time dependencies so a broken facade can never fail every command.

## Single-zone cell cohesion

A tool package whose entry callback and its hook registration are meaningless apart forms exactly one cell: both routines share one location behind a facade re-exporting the contract API, accompanied by a single cell usage document; tests and packaging files are never modeled as cells.

## Semantics-preserving transparent verification

When a verification check fails, the defect is repaired in place while preserving the approved semantics — never by deleting the offending requirement to silence the check — the check is re-run to pass, and the fail-to-pass transition is reported openly before final confirmation.
