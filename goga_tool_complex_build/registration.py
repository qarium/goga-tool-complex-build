"""Hook registration and configuration amendment routines of the comprehensive-review presets tool."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goga.config.hooks.amendments import ConfigAmendment
    from goga.hooks.tools.registration import HookRegistrar


def register_hooks(hooks: HookRegistrar) -> None:
    """Subscribe the tool's review-presets hook to the configuration amendment action.

    Args:
        hooks: Platform registration surface delivered to the facade callback.
    """

    hooks.subscribe("config", "amend_config", "review_presets", review_presets)


def review_presets(context: ConfigAmendment) -> None:
    """Contribute the four comprehensive-review presets and guard the authored strategy.

    Reads the authored `build.review.strategy` leaf (absent branches read as absent), refuses an
    authored strategy other than `full` before buffering anything, and buffers the four unconditional
    apply-where-silent amendments; the merge layer resolves authored-wins later.

    Args:
        context: Read-and-amend view over the authored configuration.

    Raises:
        ValueError: If the authored value at `build.review.strategy` is present and is not `full`.
    """

    config = context.config
    build = config.build
    review = build.review if build is not None else None
    strategy = review.strategy if review is not None else None

    if strategy is not None and strategy != "full":
        raise ValueError(
            "authored value at build.review.strategy conflicts with the tool's purpose; "
            "remove the authored strategy or uninstall the tool"
        )

    context.set("build.review.strategy", "full")
    context.set("build.review.max_iterations", 5)
    context.set("build.review.additional.patience", 1)
    context.set("build.review.additional.max_iterations", 3)
