"""Shared fixtures for the goga_tool_complex_build test suite."""

from collections.abc import Callable
from typing import Any

import pytest
from goga.config.hooks.amendments import ConfigAmendment
from goga.config.project import BuildConfig, ProjectConfig

AmendmentValue = str | int | bool | list[str]


class _RecordingAmendment(ConfigAmendment):
    """ConfigAmendment double recording every buffered call while delegating to the real buffer."""

    def __init__(self, config: ProjectConfig) -> None:
        """Stores the authored configuration and starts empty call records.

        Args:
            config: Authored configuration the view reads and amends.
        """
        super().__init__(config=config)
        self.set_calls: list[tuple[str, AmendmentValue]] = []
        self.force_calls: list[tuple[str, str, AmendmentValue]] = []

    def set(self, path: str, value: AmendmentValue) -> None:
        """Records the apply-where-silent amendment and delegates to the real buffer.

        Args:
            path: Dotted configuration leaf path.
            value: Amendment value to buffer.
        """
        self.set_calls.append((path, value))
        super().set(path, value)

    def force(self, path: str, value: AmendmentValue) -> None:
        """Records the override amendment and delegates to the real buffer.

        Args:
            path: Dotted configuration leaf path.
            value: Amendment value to buffer.
        """
        self.force_calls.append(("force", path, value))
        super().force(path, value)


class _Trap:
    """Double whose every attribute access fails the test."""

    def __getattr__(self, name: str) -> Any:
        """Fails the test with the accessed branch name.

        Args:
            name: Attribute name the production code tried to read.

        Raises:
            AssertionError: Always — the branch must never be read.
        """
        raise AssertionError(f"unread configuration branch {name!r} was accessed")


@pytest.fixture
def project_config() -> Callable[[BuildConfig | None], ProjectConfig]:
    """Returns a factory building a real authored configuration around the given build section."""

    def _build(build: BuildConfig | None) -> ProjectConfig:
        return ProjectConfig(language="python", image=None, dockerfile=None, build=build, pipeline=None)

    return _build


@pytest.fixture
def recording_view() -> Callable[[ProjectConfig], _RecordingAmendment]:
    """Returns a factory wrapping an authored configuration into a recording amendment view."""

    def _make(config: ProjectConfig) -> _RecordingAmendment:
        return _RecordingAmendment(config=config)

    return _make


@pytest.fixture
def trap() -> _Trap:
    """Returns an object whose every attribute access raises AssertionError."""
    return _Trap()
