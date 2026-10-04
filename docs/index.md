# goga-tool-complex-build

A [goga](https://pypi.org/project/goga/) hook tool that gives complex builds a comprehensive
review pass by default: the full review strategy, the review-level iteration cap, and a bounded
external review, applied wherever the project author left the review knobs unwritten.

## Documentation

Full documentation is published at <https://qarium.github.io/goga-tool-complex-build/>.

## How it works

The package registers exactly one hook — `review_presets` on the `config / amend_config`
action. At the configuration load moment the hook contributes four apply-where-silent
amendments:

- `build.review.strategy` set to `full` — the comprehensive review form;
- `build.review.max_iterations` set to `5` — the review-level iteration cap;
- `build.review.additional.patience` set to `2` and
  `build.review.additional.max_iterations` set to `3` — together bounding the external review.

Each preset applies only where the authored configuration is silent at the path. Authored-wins
is owned by the platform merge layer: the presets never overwrite authored values, a project
that already encodes its review budget keeps it, and nothing is persisted — the authored
`.goga/config.yml` stays byte-identical, and removing the tool returns the project to exactly
its authored behavior.

The one deliberate read of the authored configuration is the strategy guard. An authored
`build.review.strategy` other than `full` conflicts with the tool's purpose; it stops the
hosting command with a clean error naming the path — never the authored value — and removing
the conflicting authored value or uninstalling the tool resolves it.

## Installation

The tool has no runtime dependencies by design — the platform types are referenced under
`TYPE_CHECKING` only, so the package facade stays import-clean with or without goga installed.
The tool is installed into the project's goga docker image — the environment goga commands
run in.

### Declare it as a project dependency

Add the tool to the project's `.goga/config.yml`:

```yaml
tools:
  complex-build: latest
```

A plain `goga install` during the image build then resolves it together with the rest of the
project's declared tools:

```dockerfile
FROM <goga-base-image>

USER root

COPY . /tmp/project
RUN cd /tmp/project && goga install && rm -rf /tmp/project

USER goga
```

### Install it by name

Install the tool by name during the image build:

```dockerfile
FROM <goga-base-image>

USER root

COPY . /tmp/project
RUN cd /tmp/project && goga install complex-build && rm -rf /tmp/project

USER goga
```

## Development

The project venv lives outside the repository at `/opt/goga/project`:

```bash
/opt/goga/project/bin/pip install -e '.[test]'
/opt/goga/project/bin/python -m pytest tests/
/opt/goga/project/bin/ruff check goga_tool_complex_build/ tests/
/opt/goga/project/bin/ruff format --exclude '.usages' goga_tool_complex_build/ tests/
```

The `test` extra carries the platform (`goga>=2.0`, unpinned) and the test stack; the unpinned
platform is deliberate — a platform release that changes the amendment surface must surface
as test failures, not silent drift.

`CODEMANIFEST` and `.usages/` files are read-only contracts: when implementation and contract
disagree, the implementation is what gets fixed.
