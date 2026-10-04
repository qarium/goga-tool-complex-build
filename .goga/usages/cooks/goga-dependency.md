# Goga as the ecosystem-provided dependency

How this tool package depends on goga without carrying it as a runtime
dependency. For contributors touching imports, `pyproject.toml`, or tests.

## Policy

- The package runs inside a goga-provided interpreter: goga is never a
  runtime dependency. `[project].dependencies` stays empty — the facade
  must stay import-clean in any environment, with or without goga
  installed, because a broken facade import is fatal to every goga command.
- The package performs no runtime import of goga. Platform types the
  annotations reference (`HookRegistrar`, `ConfigAmendment`) are imported
  under `typing.TYPE_CHECKING` only; the registration and the hook talk to
  the delivered objects structurally (attribute access, `set` calls).
- Tests are the only place goga is required. Declare it exclusively in the
  test extra with a floor at the supported platform line and no upper cap:
  `goga>=2.0` — the ecosystem provides the interpreter and the version; a
  cap would fight the environment the tool actually runs in.

## Consequences

- Installing the tool adds no packages to a consumer environment.
- Test environments materialize goga through the test extra only; version
  drift is surfaced by the platform usages pin
  (`usages.github.goga.ref: 2.0.x` in `.goga/config.yml`), not by the
  package metadata.
