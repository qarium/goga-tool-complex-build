# Project rules

## Authored-value precedence

Tool-supplied config presets may fill only leaves left absent; every present value — including falsy scalars and type-mismatched values accepted at construction without runtime validation — is a deliberate authored setting that must win over any tool preset.

## Fail-fast conflict rejection

A conflict between an authored setting and a tool's purpose is rejected by raising a fixed, value-free error before any amendment is buffered or applied, and neither errors nor amendment summaries may ever expose authored values or partial amendments.

## Invalid-types coverage convention

Edge-case test suites must include an invalid-types category covering malformed scalar values that the config models accept at construction without runtime type validation, asserting the guarded rejection for each.

## Full-chain integration coverage

The test suite must include an end-to-end scenario driving the real orchestration entry point across the entire chain from discovery to merge, because silently failing links between separately tested primitives are invisible to isolated unit tests.

## Recorded-decision follow-through

Review outcomes recorded as decisions to apply are binding: the agreed changes are actually materialized in the affected artifacts rather than skipped, with the recorded decision driving the work.
