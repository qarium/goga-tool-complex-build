"""Facade of the comprehensive-review presets goga tool package."""

from .registration import register_hooks, review_presets

__all__ = ["register_hooks", "review_presets"]
